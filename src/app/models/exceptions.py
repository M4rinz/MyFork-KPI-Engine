class EmptyQueryException(Exception):
    def __init__(self, message=None):
        if message is None:
            message = "The query returned an empty dataframe"
        super().__init__(message)


class InvalidFormulaReferenceException(Exception):
    def __init__(self, message="The formula is not present in the KB"):
        super().__init__(message)


class InvalidBinaryOperatorException(Exception):
    def __init__(
        self, message="A binary operator is not present in the list of operations"
    ):
        super().__init__(message)


class InvalidKPINameException(Exception):
    def __init__(self, message="Invalid KPI name"):
        super().__init__(message)


class KPIFormulaNotFoundException(Exception):
    def __init__(self, message="KPI formula not found"):
        super().__init__(message)
