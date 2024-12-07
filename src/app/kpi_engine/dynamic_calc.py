from typing import Any

from dotenv import load_dotenv
import re
import pandas as pd
import numpy as np
from nanoid import generate
import requests

from app.kpi_engine.kpi_request import KPIRequest
import app.kpi_engine.grammar as grammar
import app.kpi_engine.exceptions as exceptions

load_dotenv()


def dynamic_kpi(
    kpi: str,
    formulas_dict: dict[str, str],
    partial_result: dict[str, Any],
    request: KPIRequest,
    **kwargs,
):
    """Processes a KPI formula string by evaluating and performing operations (D°, A°, S°, R°, C°) and resolving nested expressions. The function replaces parts of the string and recursively calls itself to process nested KPIs, returning the final computed result.

    :param kpi: The KPI formula string to be processed. It may contain nested expressions enclosed in square brackets and operations (D°, A°, S°, R°, C°).
    :type kpi: str
    :param formulas_dict: A dictionary containing predefined formulas or other necessary information for the KPI calculation.
    :type formulas_dict: dict
    :param partial_result: A partial result that is passed to calculation functions. It may contain intermediate data accumulated during processing.
    :type partial_result: any
    :param request: A request object that may contain additional parameters required for processing, for example in the context of an API or web service.
    :type request: any
    :param kwargs: Additional arguments that can be passed to the function as needed.
    :type kwargs: dict, optional

    :raises KeyError: If an operation in the KPI string does not have a corresponding function in the global scope.
    :raises ValueError: If the formula contains invalid or unrecognized expressions.

    :return: The result of the calculated KPI formula, which can be a numeric value or other data type depending on the operation and the processed formula.
    :rtype: any
    """
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
    """Executes a query on the database to retrieve real-time data based on the provided KPI string, filters, and request parameters. 
    The function processes the query result, organizes the data into a DataFrame, converts it into a NumPy array, and splits it into two parts based on a specified step.

    :param kpi: The KPI string used to build the database query. The string is parsed to extract the relevant database field for the query.
    :type kpi: str
    :param request: An object containing the request parameters, including machines, operations, start and end date, and step for splitting the data.
    :type request: KPIRequest
    :param kwargs: Additional arguments passed to the function as needed.
    :type kwargs: dict, optional

    :raises ValueError: If the KPI string is not in the expected format or the database reference is invalid.
    :raises EmptyQueryException: If the query results in an empty dataset (no data is returned from the database).

    :return: A tuple containing two NumPy arrays: 
             - The first array (`step_split`) contains the reshaped data split by the specified step.
             - The second array (`bottom`) contains any remaining data that could not be split evenly by the step.
    :rtype: tuple[np.ndarray, np.ndarray]
    """
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

    return step_split, bottom


def A(kpi: str, partial_result: dict[str, Any], **kwargs) -> str:
    """Performs an aggregation operation on a KPI, applying it to the data. The available aggregation are: mean, sum, max, min, var, std.

    :param kpi: The key performance indicator (KPI) formula to process, typically in the form of a string.
    :type kpi: str
    :param partial_result: A dictionary containing intermediate results for KPIs, used for aggregation.
    :type partial_result: dict[str, Any]
    :param kwargs: Additional optional parameters that may be passed for extended functionality.
    :type kwargs: dict, optional
    :raises ValueError: If the variable for aggregation is not found in the list of supported aggregations.
    :return: A string representing the key for the aggregated KPI result.
    :rtype: str
    """
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
    """Performs a binary operation between two KPIs, updating the partial result dictionary with the computed value.

    :param kpi: The KPI formula representing the binary operation, typically in the form of a string.
    :type kpi: str
    :param partial_result: A dictionary containing intermediate results for KPIs. It is updated with the result of the binary operation.
    :type partial_result: dict[str, Any]
    :param kwargs: Additional optional parameters for extended functionality.
    :type kwargs: dict, optional
    :raises InvalidBinaryOperatorException: If no valid binary operator is found in the list of operators.
    :return: The key representing the resulting KPI after the binary operation.
    :rtype: str
    """
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
    """Resolves a reference to another KPI by looking up the corresponding formula in the formulas dictionary and calculating it using the dynamic_kpi function.

    :param kpi: The KPI formula that includes a reference to another KPI, in the form of a string (e.g., 'R°some_formula').
    :type kpi: str
    :param partial_result: A dictionary containing intermediate results for KPIs. It is updated with the result of the referenced KPI.
    :type partial_result: dict[str, Any]
    :param formulas_dict: A dictionary mapping KPI names to their corresponding formulas. Used to look up the formula for the referenced KPI.
    :type formulas_dict: dict[str, str]
    :param request: An object containing request data such as time intervals, machines, and operations needed for KPI calculation.
    :type request: KPIRequest
    :param kwargs: Additional optional parameters for extended functionality.
    :type kwargs: dict, optional
    :raises InvalidFormulaReferenceException: If the referenced KPI formula is not found in the formulas dictionary.
    :return: The result of calculating the referenced KPI formula, as a string.
    :rtype: str
    """
    kpi_split = kpi.split("°")
    kpi_involved = kpi_split[1]

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
    """Executes a database query to retrieve data for a KPI and stores the results in the partial_result dictionary.

    :param kpi: The KPI formula that includes a database reference, used to query the database for the required data.
    :type kpi: str
    :param partial_result: A dictionary containing intermediate results for KPIs. It is updated with the results from the database query.
    :type partial_result: dict[str, Any]
    :param request: An object containing request data such as time intervals, machines, and operations needed for the database query.
    :type request: KPIRequest
    :param kwargs: Additional optional parameters for extended functionality.
    :type kwargs: dict, optional
    :return: A string representing the key for the stored results in the partial_result dictionary.
    :rtype: str
    """
    step_split, bottom = query_DB(kpi, request)
    key = generate(size=2)
    partial_result[key] = (step_split, bottom)
    return "°" + key


def C(kpi: str, partial_result: dict[str, Any], **kwargs):
    """Handles constant KPIs by storing a fixed value in the partial_result dictionary.

    :param kpi: The KPI formula representing a constant, where the constant value is provided after the '°' symbol (e.g., 'C°100').
    :type kpi: str
    :param partial_result: A dictionary containing intermediate results for KPIs. It is updated with the constant value extracted from the 'kpi' parameter.
    :type partial_result: dict[str, Any]
    :param kwargs: Additional optional parameters for extended functionality.
    :type kwargs: dict, optional
    :return: A string representing the key for the stored constant value in the partial_result dictionary.
    :rtype: str
    """
    key = generate(size=2)
    div = kpi.split("°")
    partial_result[key] = int(div[1])
    return "°" + key


def finalize_mo(
    final_formula: str, partial_result: dict[str, Any], time_aggregation: str
):
    """Finalizes the KPI calculation by applying the specified aggregation and time-based aggregation to the partial result.

    :param final_formula: The final formula representing the KPI, formatted as '°key', where 'key' corresponds to the key in the partial_result dictionary.
    :type final_formula: str
    :param partial_result: A dictionary containing partial results of KPIs. The key specified in 'final_formula' is used to access the corresponding data for aggregation.
    :type partial_result: dict[str, Any]
    :param time_aggregation: The time-based aggregation function to apply to the result (e.g., 'mean', 'sum').
    :type time_aggregation: str
    :return: The result of the aggregation after applying both the specified KPI aggregation and the time-based aggregation.
    :rtype: np.ndarray
    """
    # final formula is of the for '°key' where key is the key of the dictionary with the partial result
    key = final_formula.replace("°", "")
    result = getattr(np, "nan" + partial_result["agg"])(partial_result[key], axis=1)
    return getattr(np, "nan" + time_aggregation)(result)


def keys_involved(kpi: str, partial_result: dict[str, Any]):
    """Extracts the keys involved in a KPI formula from the partial_result dictionary.

    :param kpi: The KPI formula represented as a string, which is split by the '°' symbol to extract the variables involved.
    :type kpi: str
    :param partial_result: A dictionary containing partial results for KPIs. The function checks which keys in the formula are present in this dictionary.
    :type partial_result: dict[str, Any]
    :return: A list of keys that are present in both the KPI formula and the partial_result dictionary.
    :rtype: list[str]
    """
    sep = kpi.split("°")
    if sep[0] == "S":
        sep[2] = sep[2].replace(",", "")
    result = [i for i in sep if i in partial_result]
    return result
