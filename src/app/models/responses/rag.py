from pydantic import BaseModel, validator
from typing import Union


class KPIResponse(BaseModel):
    message: str
    value: Union[float, list[float]]

    @validator("message")
    def validate_message(cls, value):
        if not isinstance(value, str):
            raise ValueError("Message must be a string.")
        return value

    @validator("value")
    def validate_value(cls, value):
        if not isinstance(value, (int, float)):
            raise ValueError("Value must be a float or int.")
        return value
