import json

from pydantic import BaseModel


class RealTimeResponse(BaseModel):
    """Represents the response of a real-time API request.

    :param message: A message describing the response.
    :type message: str
    :param status: The HTTP status code of the response.
    :type status: int
    """
    message: str
    status: int


class RealTimeKPIResponse(BaseModel):
    """Represents a real-time KPI response, including a timestamp and a corresponding value.

    :param label: The timestamp of the KPI data.
    :type label: str
    :param value: The value of the KPI at the specified timestamp.
    :type value: float
    """
    label: str
    value: float

    def to_json(self):
        """Converts the RealTimeKPIResponse object to a JSON string.

        :return: A JSON string representation of the RealTimeKPIResponse.
        :rtype: str
        """
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)
