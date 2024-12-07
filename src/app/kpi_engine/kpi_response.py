from pydantic import BaseModel, validator


class KPIResponse(BaseModel):
    """Represents the response of a KPI computation, including a message and a value.

    :param message: A descriptive message about the KPI computation result.
    :type message: str
    :param value: The computed value of the KPI.
    :type value: float
    """

    message: str
    value: float

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

    @validator("value")
    def validate_value(cls, value):
        """Validates the value parameter to ensure it is a float or int.

        :param value: The computed KPI value.
        :type value: float or int
        :raises ValueError: If the value is not a float or int.
        :return: The validated value as a float.
        :rtype: float
        """
        
        if not isinstance(value, (int, float)):
            raise ValueError("Value must be a float or int.")
        return value
