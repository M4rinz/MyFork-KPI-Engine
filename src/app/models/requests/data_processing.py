import json

from pydantic import BaseModel


class KPIStreamingRequest(BaseModel):
    """
    Represents a request to stream KPIs for specific machines and operations.
    This request is used to provide the data preprocessing container with the necessary information to start
    an AIOKafkaConsumer stream.

    :param kpis: A list of KPIs to be streamed.
    :type kpis: list[str]
    :param machines: A list of machines involved in the KPI request.
    :type machines: list[str]
    :param operations: A list of operations related to the KPI request.
    :type operations: list[str]
    """

    kpis: list[str]
    machines: list[str]
    operations: list[str]
    special: bool

    def to_json(self):
        """
        Converts the KPIStreamingRequest object to a JSON string.

        :return: A JSON string representation of the KPIStreamingRequest.
        :rtype: str
        """
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)
