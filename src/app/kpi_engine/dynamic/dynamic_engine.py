from typing import Any

import re
import pandas as pd
import numpy as np
from nanoid import generate
import requests

import src.app.models.grammar as grammar
import src.app.models.exceptions as exceptions
from src.app.models.requests.rag import KPIRequest
from src.app.models.responses.rag import KPIResponse
from src.app.services.database import insert_aggregated_kpi
from src.app.services.knowledge_base import (
    get_kpi_formula,
    get_closest_instances,
    get_closest_kpi_formula,
)


def dynamic_kpi(
    kpi: str,
    formulas_dict: dict[str, str],
    partial_result: dict[str, Any],
    request: KPIRequest,
    **kwargs,
):
    # find the body of the innermost wrapping of the formula with []
    pattern = re.compile(r"\[([^\[\]]*)]")
    match = pattern.search(kpi)

    # if we find a match we need to recursively calculate the inner content
    if match:

        inner_content = match.group(0)
        # where to save the partial results of the recursion
        output = []
        # case in which we match S°
        if ";" in inner_content:
            left, right = inner_content.split(";")
            # the [ and ] are kept
            left = re.sub(r"[\[\]]", "", left)
            right = re.sub(r"[\[\]]", "", right)
            output.append(
                dynamic_kpi(left, formulas_dict, partial_result, request, **kwargs)
            )
            output.append(
                dynamic_kpi(right, formulas_dict, partial_result, request, **kwargs)
            )

        # case in which we do not match S°
        else:
            part = re.sub(r"[\[\]]", "", inner_content)
            output.append(
                dynamic_kpi(part, formulas_dict, partial_result, request, **kwargs)
            )

        # substitute the inner content with the calculated value with a comma to avoid infinite recursion
        remaining_string = kpi.replace(
            inner_content, str(",".join(map(str, output))), 1
        )
        return dynamic_kpi(
            remaining_string, formulas_dict, partial_result, request, **kwargs
        )

    # else we have to discover if it is a D°, A°, S°, R° or C°

    # strip the kpi from the brackets
    kpi = re.sub(r"[\[\]]", "", kpi).strip()
    # get the first letter which is always the operation
    operation = kpi[0]

    # access the function by the operation
    function = globals()[operation]

    return function(
        kpi=kpi,
        partial_result=partial_result,
        formulas_dict=formulas_dict,
        request=request,
        **kwargs,
    )


def query_DB(kpi: str, request: KPIRequest, **kwargs) -> tuple[np.ndarray, np.ndarray]:
    kpi_split = kpi.split("°")[1]

    match = re.search(r"^(.*)_(.+)$", kpi_split)
    if match:
        before_last_underscore = match.group(1)
        after_last_underscore = match.group(2)
    else:
        raise ValueError(f"DB query - invalid DB reference: {kpi_split}")

    raw_query_statement = build_query(
        request, after_last_underscore, before_last_underscore
    )

    print("Query:", raw_query_statement)

    response = requests.get(
        "http://smart-database-container:8002/query",
        params={"statement": raw_query_statement},
        timeout=10,
    )

    data = response.json()["data"]

    dataframe = pd.DataFrame(
        data,
        columns=["asset_id", "operation", "time", f"{after_last_underscore}"],
    )

    numpy_data = (
        dataframe.pivot(
            index="time",
            columns=["asset_id", "operation"],
            values=f"{after_last_underscore}",
        )
        .reset_index()
        .select_dtypes("number")
        .to_numpy()
    )

    if numpy_data.size == 0:
        raise exceptions.EmptyQueryException()

    step = request.step
    remainder = numpy_data.shape[0] % step
    bottom = None

    # the step splits perfectly
    if remainder == 0:
        step_split = numpy_data.reshape(
            numpy_data.shape[0] // step, step, numpy_data.shape[1]
        )
    # divide the numpy array in two parts, the first part is the step split and the second is the remainder
    else:
        # get the bottom part of the numpy array
        bottom = numpy_data[-remainder:]
        # bring it to three dimensions
        bottom = bottom.reshape(1, *bottom.shape)
        numpy_data = numpy_data[:-remainder]
        step_split = numpy_data.reshape(
            numpy_data.shape[0] // step, step, numpy_data.shape[1]
        )

    print("Step split shape:", step_split.shape)

    return step_split, bottom


def A(kpi: str, partial_result: dict[str, Any], **kwargs) -> str:

    # keys_inv is the key of the dictionary with the partial result associated with the kpi
    keys_inv = keys_involved(kpi, partial_result)[0]

    # get the variable on which partial_result[key] should be aggregated
    var = kpi.split("°")[2]
    # if they match the outermost aggregation, we return the key
    if var == partial_result["agg_outer_vars"] or var == "m":
        return f"°{keys_inv}"

    # time aggregation on the split of step
    for aggregation in grammar.aggregations:

        if aggregation in kpi:

            if isinstance(partial_result[keys_inv], tuple):
                np_split, np_bottom = partial_result[keys_inv]
            else:
                np_split = partial_result[keys_inv]
                np_bottom = None

            # the queried dataframe is split perfectly by the step
            if np_bottom is None:
                result = getattr(np, "nan" + aggregation)(np_split, axis=1)
                partial_result[keys_inv] = result
                return f"°{keys_inv}"

            # handle the case in which the dataframe is split in two parts: aggregate and merge them
            result_split = getattr(np, "nan" + aggregation)(np_split, axis=1)
            result_bottom = getattr(np, "nan" + aggregation)(np_bottom, axis=1)
            partial_result[keys_inv] = np.concatenate(
                (result_split, result_bottom), axis=0
            )
            return f"°{keys_inv}"

    raise ValueError(
        f"Aggregation {var} not found in the list of aggregations. The list of aggregations is {grammar.aggregations}"
    )


# pairwise operation involving two elements
def S(kpi: str, partial_result: dict[str, Any], **kwargs):
    left, right = keys_involved(kpi, partial_result)

    op = next((op for op in grammar.operators if op in kpi), None)
    if op:
        # Perform the operation and update the partial result
        partial_result[left] = eval(f"partial_result[left] {op} partial_result[right]")
        return f"°{left}"

    raise exceptions.InvalidBinaryOperatorException(
        f"Binary operator not found in the list of operations: {grammar.operators}"
    )


def R(
    kpi: str,
    partial_result: dict[str, Any],
    formulas_dict: dict[str, str],
    request: KPIRequest,
    **kwargs,
):

    kpi_split = kpi.split("°")
    kpi_involved = kpi_split[1]
    operation = kpi_split[4]

    # save the operation if it is in the formula
    if operation in grammar.operations:
        partial_result.setdefault("internal_operation", []).append(operation)

    if kpi_involved in formulas_dict:
        return str(
            dynamic_kpi(
                formulas_dict[kpi_involved],
                formulas_dict,
                partial_result,
                request,
                **kwargs,
            )
        )

    raise exceptions.InvalidFormulaReferenceException(
        f"KPI {kpi} not found in the list of KPIs. The list of KPIs is {formulas_dict.keys()}"
    )


def D(
    kpi: str,
    partial_result: dict[str, Any],
    request: KPIRequest,
    **kwargs,
):

    if (
        "internal_operation" in partial_result
        and len(partial_result["internal_operation"]) != 0
    ):
        op = partial_result["internal_operation"].pop(0)
        if len(request.operations) != 0:
            request.operations = [op] * len(request.operations)
        elif len(request.machines) != 0:
            request.operations = [op] * len(request.machines)
        else:
            request.operations = [op]

    step_split, bottom = query_DB(kpi, request)
    key = generate(size=2)
    partial_result[key] = (step_split, bottom)
    return "°" + key


def C(kpi: str, partial_result: dict[str, Any], **kwargs):
    key = generate(size=2)
    div = kpi.split("°")
    partial_result[key] = int(div[1])
    return "°" + key


def compute(request: KPIRequest, chart: bool) -> KPIResponse:
    name = request.name

    # fare funzione controllo della stringa
    # validate machines and operations
    # vado ad aggiungere un ulterione controllo

    request.machines, request.operations = check_machine_operation(
        request.machines, request.operations
    )
    # if len(machines) != len(operations):
    # return KPIResponse(
    # message="Invalid number of machines and operations", value=-1
    # )
    # get the formula from the KB
    try:
        formulas = get_kpi_formula(name)
        name = next(iter(formulas))

        if not formulas:
            formulas = get_closest_kpi_formula(name)
            formulas = formulas["formulas"]
            name = next(iter(formulas))

    except Exception as e:
        return KPIResponse(message=repr(e), value=-1)

    start_date = request.start_date
    end_date = request.end_date
    aggregation = request.time_aggregation

    # inits the kpi calculation by finding the outermost aggregation and involved aggregation variables

    partial_result = preprocessing(name, formulas)

    try:
        # computes the final matrix that has to be aggregated for mo and time_aggregation
        result = dynamic_kpi(formulas[name], formulas, partial_result, request)
    except Exception as e:
        return KPIResponse(message=repr(e), value=-1)

    print("Partial Results:", partial_result, "Result:", result)

    # aggregated on time
    if not chart:
        result = finalize_mo(result, partial_result, request.time_aggregation)
    else:
        result = finalize_mo(result, partial_result, None)

    message = (
        f"The {aggregation} of KPI {name} for machines {request.machines} with operations {request.operations} "
        f"from {start_date} to {end_date} is {result}"
    )

    print("Message:", message)

    if not chart:
        _ = insert_aggregated_kpi(
            request=request,
            kpi_list=formulas.keys(),
            value=result,
        )

    return KPIResponse(message=message, value=result)


def preprocessing(kpi_name: str, formulas_dict: dict[str, Any]) -> dict[str, Any]:
    partial_result = {}
    # get the actual formula of the kpi
    kpi_formula = formulas_dict[kpi_name]
    # get the variables of the aggregation
    search_var = kpi_formula.split("°")
    # split because we always have [ after the last match of the aggregation
    aggregation_variables = search_var[2].split("[")
    if search_var[1] in grammar.aggregations:
        partial_result["agg_outer_vars"] = aggregation_variables[0]
        partial_result["agg"] = search_var[1]
    else:
        partial_result["agg_outer_vars"] = ""
        partial_result["agg"] = ""

    return partial_result


def finalize_mo(
    final_formula: str, partial_result: dict[str, Any], time_aggregation: str
):
    # final formula is of the for '°key' where key is the key of the dictionary with the partial result
    key = final_formula.replace("°", "")
    result = partial_result[key]
    if partial_result["agg"] != "":
        result = getattr(np, "nan" + partial_result["agg"])(result, axis=1)
    if time_aggregation is None:
        return np.nan_to_num(result).tolist()
    return getattr(np, "nan" + time_aggregation)(result)


def keys_involved(kpi: str, partial_result: dict[str, Any]):
    sep = kpi.split("°")
    if sep[0] == "S":
        sep[2] = sep[2].replace(",", "")
    result = [i for i in sep if i in partial_result]
    return result


def check_machine_operation(machines, operations):
    if isinstance(machines, str):
        try:
            machine = get_closest_instances(machines)["instances"]
        except Exception as e:
            return KPIResponse(message=repr(e), value=-1)

        if machine:
            if len(machine) == len(operations):
                return machine, operations
            elif len(machine) < len(operations):
                return KPIResponse(
                    message="Invalid number of machines and operations", value=-1
                )
            else:
                operations.extend(["independent"] * (len(machine) - len(operations)))
                if len(machine) == len(operations):
                    return machine, operations
                else:
                    return KPIResponse(
                        message="Invalid number of machines and operations", value=-1
                    )
        return machine, operations

    if machines and operations:
        if len(machines) != len(operations):
            return KPIResponse(
                message="Invalid number of machines and operations", value=-1
            )
        return machines, operations

    return machines, operations


# build query statement
def build_query(request: KPIRequest, after_last_underscore, before_last_underscore):
    if request.machines and request.operations:
        conditions = " OR ".join(
            f"(name = '{m}' AND operation = '{o}')"
            for m, o in zip(request.machines, request.operations)
        )
    elif request.machines:
        conditions = " OR ".join(f"(name = '{m}')" for m in request.machines)
    elif request.operations:
        conditions = " OR ".join(f"(operation = '{o}')" for o in request.operations)
    else:
        conditions = ""

    raw_query_statement = f"""
    SELECT asset_id, operation, time, {after_last_underscore} 
    FROM real_time_data 
    WHERE kpi = '{before_last_underscore}'
    """

    if conditions:
        raw_query_statement += f"AND ({conditions}) "

    raw_query_statement += (
        f"AND time BETWEEN '{request.start_date}' AND '{request.end_date}'"
    )

    return raw_query_statement
