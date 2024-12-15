import numpy as np
import requests

from src.app.models.requests.rag import KPIRequest


def insert_aggregated_kpi(
    request: KPIRequest,
    kpi_list: list,
    value: np.float64,
):
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

    print("Inserting aggregated KPI data into the database...")

    return requests.post(
        "http://smart-database-container:8002/insert",
        timeout=5,
    )
