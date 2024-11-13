""" KPI Calculation Engine. """

from .kpi_request import KPIRequest
from .kpi_response import KPIResponse

from sqlalchemy.orm import Session
import requests
import re
import pandas as pd
import numpy as np
import numexpr

from ..models import RealTimeData


class KPIEngine:
    def __init__(self):
        pass

    @staticmethod
    def compute(
            historical_data: Session,
            real_time_data: Session,
            details: KPIRequest
    ) -> KPIResponse:

        name = details.name
        machine = details.machine

        # Get the formula from the KB
        formula = get_kpi_formula(name, machine)

        if formula is None:
            return KPIResponse("Invalid KPI name or machine", -1)

        aggregation = details.aggregation
        start_date = details.start_date
        end_date = details.end_date

        involved_kpis = set(re.findall(r"\b[A-Za-z][A-Za-z0-9]*\b", formula))

        # SELECT kpi, time, value FROM RealTimeData
        # WHERE kpi IN (involved_kpis)
        # AND machine = machine
        # AND time between start_date, end_date

        raw_query_statement = real_time_data.query(RealTimeData).filter(
            RealTimeData.kpi.in_(involved_kpis),
            RealTimeData.name == machine,
            RealTimeData.time.between(start_date, end_date)
        ).with_entities(
            RealTimeData.kpi,
            RealTimeData.time,
            RealTimeData.value
        ).statement


        dataframe = pd.read_sql(raw_query_statement, real_time_data.bind)

        # Here we assume KPIs calculation is bound to a single machine
        pivot_table = dataframe.pivot(
            index="time", columns="kpi", values="value"
        ).reset_index()

        for base_kpi in involved_kpis:
            globals()[base_kpi] = pivot_table[base_kpi]

        # Calculate the KPI
        partial_result = numexpr.evaluate(formula)
        result = getattr(np, aggregation)(partial_result)
        message = f"The {aggregation} of KPI {name} for {machine} from {start_date} to {end_date} is {result}"

        return KPIResponse(message, result)


def get_kpi_formula(name: str, machine: str):
    """
    Get the formula for the KPI from the KB

    :param name: the name of the KPI to get the formula for
    :param machine: the machine to get the formula for
    :return: the formula for the KPI
    """
    api_url = f"http://KB:8000/{name}?machine={machine}"
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            raise InvalidKPINameException()
    except requests.exceptions.RequestException as e:
        print(f"Error making GET request: {e}")
        return None


class InvalidKPINameException(Exception):
    def __init__(self):
        super().__init__("Invalid KPI name")