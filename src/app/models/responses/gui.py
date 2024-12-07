import json
from datetime import datetime

from pydantic import BaseModel


class RealTimeKPIResponse(BaseModel):
    label: datetime
    value: float

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)
