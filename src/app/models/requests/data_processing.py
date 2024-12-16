import json

from pydantic import BaseModel


class KPIStreamingRequest(BaseModel):
    kpis: list[str]  # lis of all kpis
    machines: list[str]  # list of all machines
    operations: list[str]  # list of all operations
    special: bool

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)
