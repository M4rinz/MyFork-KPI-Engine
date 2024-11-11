""" KPI Request interface for incoming requests. """

from datetime import datetime
import src.main.app.services.grammar as grammar


class KPIRequest:
    """
    KPI Request details for incoming requests. A request should contain:
    - KPI name
    - Machine name
    - Aggregation function
    - Start date
    - End date
    """

    def __init__(self, name, machine, aggregation, start_date, end_date):
        self.name = name
        self.machine = machine
        self.aggregation = aggregation
        self.start_date = start_date
        self.end_date = end_date

    @property
    def name(self):
        return self._name

    @property
    def start_date(self):
        return self._start_date

    @property
    def end_date(self):
        return self._end_date

    @property
    def machine(self):
        return self._machine

    @property
    def aggregation(self):
        return self._aggregation

    @end_date.setter
    def end_date(self, value):
        if datetime != type(value):
            raise ValueError("KPI Details: end_date must be a datetime object.")
        self._end_date = value

    @start_date.setter
    def start_date(self, value):

        if datetime != type(value):
            raise ValueError("KPI Details: start_date must be a datetime object.")
        self._start_date = value

    @name.setter
    def name(self, value):

        if not isinstance(value, str):
            raise ValueError("KPI Details: KPI name must be a string.")
        self._name = value

    @machine.setter
    def machine(self, value):
        if not isinstance(value, str):
            raise ValueError("KPI Details: Machine name must be a string.")
        self._machine = value

    @aggregation.setter
    def aggregation(self, value):
        if not isinstance(value, str):
            raise ValueError("KPI Details: Aggregation must be a string.")
        if value not in grammar.aggregations:
            raise ValueError(
                f"KPI Details: Invalid aggregation function. Must be one of {grammar.aggregations}"
            )
        self._aggregation = value
