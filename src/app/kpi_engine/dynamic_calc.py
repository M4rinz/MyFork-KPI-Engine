from typing import Any

import psycopg2.extensions
from dotenv import load_dotenv
import re
import pandas as pd
import numpy as np
from nanoid import generate

from src.app.kpi_engine.kpi_request import KPIRequest
import src.app.kpi_engine.grammar as grammar
import src.app.kpi_engine.exceptions as exceptions

load_dotenv()


def dynamic_kpi(
    kpi: str,
    formulas_dict: dict[str, str],
    partial_result: dict[str, Any],
    connection: psycopg2.extensions.connection,
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
                dynamic_kpi(
                    left, formulas_dict, partial_result, connection, request, **kwargs
                )
            )
            output.append(
                dynamic_kpi(
                    right, formulas_dict, partial_result, connection, request, **kwargs
                )
            )

        # case in which we do not match S°
        else:
            part = re.sub(r"[\[\]]", "", inner_content)
            output.append(
                dynamic_kpi(
                    part, formulas_dict, partial_result, connection, request, **kwargs
                )
            )

        # substitute the inner content with the calculated value with a comma to avoid infinite recursion
        remaining_string = kpi.replace(
            inner_content, str(",".join(map(str, output))), 1
        )
        return dynamic_kpi(
            remaining_string,
            formulas_dict,
            partial_result,
            connection,
            request,
            **kwargs,
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
        connection=connection,
        request=request,
        **kwargs,
    )


def query_DB(
    kpi: str, connection: psycopg2.extensions.connection, request: KPIRequest, **kwargs
) -> tuple[np.ndarray, np.ndarray]:

    kpi_split = kpi.split("°")[1]

    match = re.search(r"^(.*)_(.+)$", kpi_split)
    if match:
        before_last_underscore = match.group(1)
        after_last_underscore = match.group(2)
    else:
        raise ValueError(f"DB query - invalid DB reference: {kpi_split}")

    raw_query_statement = f"""
    SELECT asset_id, operation, time, {after_last_underscore} 
    FROM real_time_data 
    WHERE kpi = '{before_last_underscore}'
    AND ( 
    """

    for m, o in zip(request.machines, request.operations):
        raw_query_statement += f"(name = '{m}' AND operation = '{o}') OR "
    raw_query_statement = raw_query_statement[:-4]

    raw_query_statement += f"""
    )
    AND time BETWEEN '{request.start_date}' AND '{request.end_date}'
    """

    cursor = connection.cursor()
    cursor.execute(raw_query_statement)

    dataframe = pd.DataFrame(
        cursor.fetchall(),
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

    return step_split, bottom


def A(kpi: str, partial_result: dict[str, Any], **kwargs) -> str:

    # keys_inv is the key of the dictionary with the partial result associated with the kpi
    keys_inv = keys_involved(kpi, partial_result)[0]

    # get the variable on which partial_result[key] should be aggregated
    var = kpi.split("°")[2]

    # if they match the outermost aggregation, we return the key
    if var == partial_result["agg_outer_vars"]:
        return f"°{keys_inv}"

    # time aggregation on the split of step
    for aggregation in grammar.aggregations:
        if aggregation in kpi:
            np_split, np_bottom = partial_result[keys_inv]

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
    connection: psycopg2.extensions.connection,
    request: KPIRequest,
    **kwargs,
):

    kpi_split = kpi.split("°")
    kpi_involved = kpi_split[1]

    if kpi_involved in formulas_dict:
        return str(
            dynamic_kpi(
                formulas_dict[kpi_involved],
                formulas_dict,
                partial_result,
                connection,
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
    connection: psycopg2.extensions.connection,
    request: KPIRequest,
    **kwargs,
):

    step_split, bottom = query_DB(kpi, connection, request)
    key = generate(size=2)
    partial_result[key] = (step_split, bottom)
    return "°" + key


def C(kpi: str, partial_result: dict[str, Any], **kwargs):

    key = generate(size=2)
    div = kpi.split("°")
    partial_result[key] = int(div[1])
    return "°" + key


def finalize_mo(
    final_formula: str, partial_result: dict[str, Any], time_aggregation: str
):

    # final formula is of the for '°key' where key is the key of the dictionary with the partial result
    key = final_formula.replace("°", "")
    result = getattr(np, "nan" + partial_result["agg"])(partial_result[key], axis=1)
    return getattr(np, "nan" + time_aggregation)(result)


def keys_involved(kpi: str, partial_result: dict[str, Any]):
    sep = kpi.split("°")
    if sep[0] == "S":
        sep[2] = sep[2].replace(",", "")
    result = [i for i in sep if i in partial_result]
    return result
