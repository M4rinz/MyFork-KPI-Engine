from pydantic import BaseModel, validator
from typing import Union


class KPIResponse(BaseModel):
    """Represents the response of a KPI computation, including a message and a value.

    :param message: A descriptive message about the KPI computation result.
    :type message: str
    :param value: The computed value of the KPI.
    :type value: float
    """

    message: str
    value: Union[float, list[float]]

    @validator("message")
    def validate_message(cls, value):
        """Validates the message parameter to ensure it is a string.

        :param value: The message describing the KPI computation result.
        :type value: str
        :raises ValueError: If the message is not a string.
        :return: The validated message.
        :rtype: str
        """

        if not isinstance(value, str):
            raise ValueError("Message must be a string.")
        return value
