from datetime import datetime

from pydantic import BaseModel


class RealTimeKPIRequest(BaseModel):
    name: str
    machines: list
    operations: list
    time_aggregation: str
    start_date: datetime  # (YYYY-MM-DD HH:MM:SS)
