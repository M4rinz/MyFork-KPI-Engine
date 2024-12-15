from pydantic import BaseModel


class RealTimeKPI(BaseModel):
    """Represents a real-time KPI, containing the KPI name, the column name, 
    and a list of associated values.

    :param kpi: The name of the KPI.
    :type kpi: str
    :param column: The name of the column representing the data associated 
        with the KPI.
    :type column: str
    :param values: A list of values associated with the KPI.
    :type values: list[float]
    """
    kpi: str
    column: str
    operation: str
    values: list[float]

    @classmethod
    def from_json(cls, data):
        """Creates an instance of the RealTimeKPI class from a dictionary.

        :param data: A dictionary containing the KPI data with the keys 
            'kpi', 'column', and 'values'.
        :type data: dict
        :return: An instance of the RealTimeKPI class initialized with the 
            dictionary data.
        :rtype: RealTimeKPI
        """
        return cls(
            kpi=data["kpi"],
            column=data["column"],
            operation=data["operation"],
            values=data["values"],
        )
