""" KPI Result for responses. """


class KPIResponse:
    def __init__(self, message, value):
        self.message = message
        self.value = value

    @property
    def message(self):
        return self._message

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    @message.setter
    def message(self, value):
        self._message = value
