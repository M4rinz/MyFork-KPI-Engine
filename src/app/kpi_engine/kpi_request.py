from datetime import datetime
from pydantic import BaseModel, validator
from src.app.kpi_engine import grammar


class KPIRequest(BaseModel):
    """
    KPI Request details for incoming requests. A request should contain:
    - KPI name
    - Machine name
    - Aggregation function
    - Start date
    - End date
    """

    name: str
    machine: str
    aggregation: str
    start_date: datetime
    end_date: datetime

    @validator("start_date", "end_date", pre=True)
    def validate_datetime(cls, value):
        if not isinstance(value, datetime):
            raise ValueError("The date must be a datetime object.")
        return value

    @validator("name")
    def validate_name(cls, value):
        if not isinstance(value, str):
            raise ValueError("KPI name must be a string.")
        return value

    @validator("machine")
    def validate_machine(cls, value):
        if not isinstance(value, str):
            raise ValueError("Machine name must be a string.")
        return value

    @validator("aggregation")
    def validate_aggregation(cls, value):
        if not isinstance(value, str):
            raise ValueError("Aggregation function must be a string.")
        if value not in grammar.aggregations:
            raise ValueError(
                f"Invalid aggregation function. Must be one of {grammar.aggregations}"
            )
        return value
