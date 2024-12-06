import json
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
    machines: list
    operations: list
    time_aggregation: str
    start_date: datetime
    end_date: datetime
    step: int

    @validator("name")
    def validate_name(cls, value):
        if not isinstance(value, str):
            raise ValueError("KPI name must be a string.")
        return value

    @validator("machines")
    def validate_machines(cls, value):
        if not isinstance(value, list):
            raise ValueError("Machine name must be a list.")
        return value

    @validator("operations")
    def validate_operations(cls, value):
        if not isinstance(value, list):
            raise ValueError("Operation name must be a list.")
        return value

    @validator("step")
    def validate_step(cls, value):
        if not isinstance(value, int):
            raise ValueError("The step must be a integer.")
        if value < 0:
            raise ValueError("The step must be a positive integer.")
        return value

    @validator("time_aggregation")
    def validate_time_aggregation(cls, value):
        if not isinstance(value, str):
            raise ValueError("Aggregation function must be a string.")
        if value not in grammar.aggregations:
            raise ValueError(
                f"Invalid aggregation function. Must be one of {grammar.aggregations}"
            )
        return value


class RealTimeRequest(BaseModel):
    name: str
    machines: list
    operations: list
    time_aggregation: str
    start_date: datetime  # (YYYY-MM-DD HH:MM:SS)


class KPIStreamingRequest(BaseModel):
    kpis: list[str]  # lis of all kpis
    machines: list[str]  # list of all machines
    operations: list[str]  # list of all operations

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)


class RealTimeKPI(BaseModel):
    kpi: str
    machine: str
    operation: str
    column: str
    value: float

    @classmethod
    def from_json(cls, data):
        return cls(
            kpi=data["kpi"],
            machine=data["machine"],
            operation=data["operation"],
            column=data["column"],
            value=data["value"],
        )
