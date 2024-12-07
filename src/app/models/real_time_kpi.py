from pydantic import BaseModel


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
