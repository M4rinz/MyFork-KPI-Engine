import json

from pydantic import BaseModel


class RealTimeResponse(BaseModel):
    message: str
    status: int


class RealTimeKPIResponse(BaseModel):
    label: str
    value: float

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)
