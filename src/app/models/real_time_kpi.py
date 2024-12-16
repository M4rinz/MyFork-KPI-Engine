from pydantic import BaseModel


class RealTimeKPI(BaseModel):
    kpi: str
    column: str
    operation: str
    values: list[float]

    @classmethod
    def from_json(cls, data):
        return cls(
            kpi=data["kpi"],
            column=data["column"],
            operation=data["operation"],
            values=data["values"],
        )
