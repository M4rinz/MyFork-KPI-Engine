import numpy as np
import requests

#from src.app.models.requests.rag import KPIRequest
from app.models.requests.rag import KPIRequest


def insert_aggregated_kpi(
    request: KPIRequest,
    kpi_list: list,
    value: np.float64,
):
    """Inserts the aggregated KPI result into the database.

    This function constructs an SQL `INSERT` query to store the aggregated KPI data 
    into a database. It inserts details such as the KPI name, the aggregated value, 
    the relevant machines and operations, and the list of KPIs involved in the aggregation.

    :param request: The KPI request containing details such as name, machines, 
                    operations, and date range for the aggregation.
    :type request: KPIRequest
    :param kpi_list: A list of KPIs that were involved in the aggregation.
    :type kpi_list: list
    :param value: The aggregated KPI value calculated from the input KPIs.
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

    print("Inserting aggregated KPI data into the database...")

    return requests.post(
        "http://smart-database-container:8002/insert",
        json={"statement": insert_query, "data": data},
        timeout=5,
    )
