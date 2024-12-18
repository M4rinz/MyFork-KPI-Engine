from pydantic import BaseModel
from typing import Union


class KPIResponse(BaseModel):
    """
    Represents the response of a KPI computation, including a message and a value.
    This response is sent to the RAG after the kpi computation is completed, as well as the GUI in case of a chart
    request.

    :param message: A descriptive message about the KPI computation result.
    :type message: str
    :param value: The computed value of the KPI if time-aggregated, or a list of values.
    :type value: union[float, list[float]]
    """

    message: str
    value: Union[float, list[float]]
