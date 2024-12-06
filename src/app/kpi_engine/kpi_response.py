import json
from datetime import datetime

from pydantic import BaseModel, validator


class KPIResponse(BaseModel):
    message: str
    value: float

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


class RealTimeKPIResponse(BaseModel):
    label: datetime
    value: float

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)


class RealTimeResponse(BaseModel):
    message: str
    status: int
