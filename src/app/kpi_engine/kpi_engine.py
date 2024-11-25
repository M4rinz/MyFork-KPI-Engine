"""KPI Calculation Engine."""

from src.app.kpi_engine.kpi_request import KPIRequest
from src.app.kpi_engine.kpi_response import KPIResponse
from src.app.models import RealTimeData, AggregatedKPI
import src.app.test_rec as din
from sqlalchemy.orm import Session
import requests
import re
import pandas as pd
import numpy as np
import numexpr


class KPIEngine:
    @staticmethod
    def compute(db: Session, details: KPIRequest) -> KPIResponse:
        name = details.name
        machine = details.machine

        # Get the formula from the KB
        # va levata machine dalla richiesta alla knowledge base
        formula = get_kpi_formula(name)

        if formula is None:
            return KPIResponse(message="Invalid KPI name or machine", value=-1)

        aggregation = details.aggregation
        start_date = details.start_date
        end_date = details.end_date
        operations= details.operation
        step= details.step


        involved_kpis = set(re.findall(r"\b[A-Za-z][A-Za-z0-9]*\b", formula))

        # SELECT kpi, time, value FROM RealTimeData
        # WHERE kpi IN (involved_kpis)
        # AND machine = machine
        # AND time between start_date, end_date

        raw_query_statement = (
            db.query(RealTimeData)
            .filter(
                RealTimeData.kpi.in_(involved_kpis),
                RealTimeData.name == machine,
                RealTimeData.time.between(start_date, end_date),
            )
            .with_entities(RealTimeData.kpi, RealTimeData.time, RealTimeData.avg)
            .statement
        )

        dataframe = pd.read_sql(raw_query_statement, db.bind)

        # Here we assume KPIs calculation is bound to a single machine (non vale più questa assunzione)
        pivot_table = dataframe.pivot(
            index="time", columns="kpi", values="value"
        ).reset_index()

        # region TODO: Implement the KPI calculation, refactor
        for base_kpi in involved_kpis:
            globals()[base_kpi] = pivot_table[base_kpi]
        partial_result = numexpr.evaluate(formula)
        # endregion

        result = float(getattr(np, aggregation)(partial_result))
        message = (
            f"The {aggregation} of KPI {name} for {machine} "
            f"from {start_date} to {end_date} is {result}"
        )

        insert_aggregated_kpi(
            db=db,
            name=name,
            machine=machine,
            result=result,
            start_date=start_date,
            end_date=end_date,
        )

        return KPIResponse(message=message, value=result)


def insert_aggregated_kpi(
    db: Session, name: str, machine: str, result: float, start_date, end_date
):
    aggregated_kpi = AggregatedKPI(
        aggregated_kpi_name=name,
        value=result,
        begin=start_date,
        end=end_date,
        asset_id=machine,
    )

    db.add(aggregated_kpi)
    db.commit()
    db.refresh(aggregated_kpi)


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
