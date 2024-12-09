from datetime import datetime
from typing import Union
from pydantic import BaseModel, validator

from src.app.models import grammar


class KPIRequest(BaseModel):
    """Represents the details of a KPI request, including the KPI name, machines, operations,
    aggregation function, and time range.

    :param name: The name of the KPI to be calculated.
    :type name: str
    :param machines: A list of machines involved in the KPI calculation.
    :type machines: list
    :param operations: A list of operations corresponding to the machines.
    :type operations: list
    :param time_aggregation: The time aggregation function to be applied (e.g., 'daily', 'weekly').
    :type time_aggregation: str
    :param start_date: The start date of the KPI calculation range.
    :type start_date: datetime
    :param end_date: The end date of the KPI calculation range.
    :type end_date: datetime
    :param step: The calculation step, representing the time intervals for aggregation.
                 Must be a positive integer.
    :type step: int
    """

    name: str
    machines: Union[list, str]
    operations: list
    time_aggregation: str
    start_date: datetime
    end_date: datetime
    step: int

    @validator("name")
    def validate_name(cls, value):
        """Validates the KPI name to ensure it is a string.

        :param value: The name of the KPI.
        :type value: str
        :raises ValueError: If the KPI name is not a string.
        :return: The validated KPI name.
        :rtype: str
        """

        if not isinstance(value, str):
            raise ValueError("KPI name must be a string.")
        return value

    @validator("machines")
    def validate_machines(cls, value):
        """Validates the machines parameter to ensure it is a list.

        :param value: The list of machines.
        :type value: list
        :raises ValueError: If machines is not a list.
        :return: The validated machines list.
        :rtype: list
        """

        if not isinstance(value, (list, str)):
            raise ValueError("Machine name must be a list or a string.")
        return value

    @validator("operations")
    def validate_operations(cls, value):
        """Validates the operations parameter to ensure it is a list.

        :param value: The list of operations.
        :type value: list
        :raises ValueError: If operations is not a list.
        :return: The validated operations list.
        :rtype: list
        """

        if not isinstance(value, list):
            raise ValueError("Operation name must be a list.")
        return value

    @validator("step")
    def validate_step(cls, value):
        """
        Validates the step parameter to ensure it is a positive integer.

        :param value: The calculation step.
        :type value: int
        :raises ValueError: If the step is not a positive integer.
        :return: The validated step value.
        :rtype: int
        """

        if not isinstance(value, int):
            raise ValueError("The step must be a integer.")
        if value < 0:
            raise ValueError("The step must be a positive integer.")
        return value

    @validator("time_aggregation")
    def validate_time_aggregation(cls, value):
        """
        Validates the time aggregation function to ensure it is a string
        and matches one of the predefined options in the grammar module.

        :param value: The time aggregation function.
        :type value: str
        :raises ValueError: If the aggregation function is not a valid option.
        :return: The validated aggregation function.
        :rtype: str
        """

        if not isinstance(value, str):
            raise ValueError("Aggregation function must be a string.")
        if value not in grammar.aggregations:
            raise ValueError(
                f"Invalid aggregation function. Must be one of {grammar.aggregations}"
            )
        return value
