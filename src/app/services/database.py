import numpy as np
import requests

from src.app.models.requests.rag import KPIRequest


def insert_aggregated_kpi(
    request: KPIRequest,
    kpi_list: list,
    value: np.float64,
):

    data = {
        "name": request.name,
        "aggregated_value": value.item(),
        "begin_datetime": str(request.start_date),
        "end_datetime": str(request.end_date),
        "kpi_list": list(kpi_list),
        "operations": request.operations,
        "machines": request.machines,
        "step": request.step,
    }

    print("Inserting aggregated KPI data into the database...", data)

    return requests.post(
        "http://smart-database-container:8002/insert_aggregated_kpi",
        json=data,
        timeout=5,
    )
