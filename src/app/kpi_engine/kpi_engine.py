"""KPI Calculation Engine."""

import numpy as np
import requests

#from src.app.kpi_engine.kpi_request import KPIRequest
#from src.app.kpi_engine.kpi_response import KPIResponse
#import src.app.kpi_engine.dynamic_calc as dyn
#import src.app.kpi_engine.exceptions as exceptions

from app.kpi_engine.kpi_request import KPIRequest
from app.kpi_engine.kpi_response import KPIResponse
import app.kpi_engine.dynamic_calc as dyn
import app.kpi_engine.exceptions as exceptions

from typing import Any


class KPIEngine:
    @staticmethod
    def compute(request: KPIRequest) -> KPIResponse:
        """This class handles the computation of Key Performance Indicators (KPIs).

        The class interacts with the knowledge base to fetch formulas, preprocesses the KPI computation logic,
        and utilizes dynamic calculations to compute and aggregate the required KPIs.
        """
        name = request.name
        machines = request.machines
        operations = request.operations

        # validate machines and operations
        if len(machines) != len(operations):
            return KPIResponse(
                message="Invalid number of machines and operations", value=-1
            )

        # get the formula from the KB
        try:
            formulas = get_kpi_formula(name)
        except Exception as e:
            return KPIResponse(message=repr(e), value=-1)

        start_date = request.start_date
        end_date = request.end_date
        aggregation = request.time_aggregation

        # inits the kpi calculation by finding the outermost aggregation and involved aggregation variables
        partial_result = preprocessing(name, formulas)

        try:
            # computes the final matrix that has to be aggregated for mo and time_aggregation
            result = dyn.dynamic_kpi(formulas[name], formulas, partial_result, request)
        except Exception as e:
            return KPIResponse(message=repr(e), value=-1)

        # aggregated on time
        result = dyn.finalize_mo(result, partial_result, request.time_aggregation)

        message = (
            f"The {aggregation} of KPI {name} for machines {machines} with operations {operations} "
            f"from {start_date} to {end_date} is {result}"
        )

        insert_aggregated_kpi(
            request=request,
            kpi_list=formulas.keys(),
            value=result,
        )

        return KPIResponse(message=message, value=result)


def preprocessing(kpi_name: str, formulas_dict: dict[str, Any]) -> dict[str, Any]:
    """Preprocesses the KPI formula to extract aggregation variables and operations.

    :param kpi_name: The name of the KPI.
    :type kpi_name: str
    :param formulas_dict: Dictionary containing KPI formulas.
    :type formulas_dict: dict[str, Any]
    :return: A dictionary with aggregation variables and operations.
    :rtype: dict[str, Any]
    """
    partial_result = {}
    # get the actual formula of the kpi
    kpi_formula = formulas_dict[kpi_name]
    # get the variables of the aggregation
    search_var = kpi_formula.split("°")
    # split because we always have [ after the last match of the aggregation
    aggregation_variables = search_var[2].split("[")
    partial_result["agg_outer_vars"] = aggregation_variables[0]
    partial_result["agg"] = search_var[1]
    return partial_result


def insert_aggregated_kpi(
    request: KPIRequest,
    kpi_list: list,
    value: np.float64,
):
    """Inserts the aggregated KPI result into the database.

    :param request: The KPI request containing details like name, machines, and operations.
    :type request: KPIRequest
    :param kpi_list: List of KPIs involved in the aggregation.
    :type kpi_list: list
    :param value: The aggregated KPI value.
    :type value: np.float64
    :return: The response from the database after insertion.
    :rtype: requests.Response
    """
    insert_query = """
        INSERT INTO aggregated_kpi (name, aggregated_value, begin_datetime, end_datetime, kpi_list, operations, machines, step)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """

    data = (
        request.name,
        value.item(),
        str(request.start_date),
        str(request.end_date),
        list(kpi_list),
        request.operations,
        request.machines,
        request.step,
    )

    return requests.post(
        "http://smart-database-container:8002/insert",
        json={"statement": insert_query, "data": data},
        timeout=5,
    )


def get_kpi_formula(name: str) -> dict[str, str]:
    """Fetches the KPI formula from the knowledge base.

    :param name: The name of the KPI.
    :type name: str
    :raises exceptions.KPIFormulaNotFoundException: If the KPI formula is not found.
    :return: A dictionary containing KPI formulas.
    :rtype: dict[str, str]
    """
    response = requests.get(
        "http://kb-service-container:8001/get_formulas",
        params={"kpi_label": name},
        timeout=5,
    )
    if response.status_code != 200:
        raise exceptions.KPIFormulaNotFoundException()
    return response.json()
