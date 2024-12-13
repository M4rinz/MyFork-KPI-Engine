from datetime import datetime


class RealTimeKPIRequest:
    name: str
    machines: list
    operations: list
    time_aggregation: str
    start_date: datetime  # (YYYY-MM-DD HH:MM:SS)

    def __init__(self, name, machines, operations, time_aggregation, start_date):
        self.name = name
        self.machines = machines
        self.operations = operations
        self.time_aggregation = time_aggregation
        self.start_date = start_date
