class EmptyQueryException(Exception):
    """Exception raised when a query returns an empty dataframe.

    :param message: The error message to be associated with the exception, defaults to "The query returned an empty dataframe"
    :type message: str, optional
    """
    def __init__(self, message=None):
        if message is None:
            message = "The query returned an empty dataframe"
        super().__init__(message)


class InvalidFormulaReferenceException(Exception):
    """Exception raised when a formula is not found in the knowledge base (KB).

    :param message: The error message to be associated with the exception, defaults to "The formula is not present in the KB"
    :type message: str, optional
    """
    def __init__(self, message="The formula is not present in the KB"):
        super().__init__(message)


class InvalidBinaryOperatorException(Exception):
    """Exception raised when a binary operator is not found in the list of available operations.

    :param message: The error message to be associated with the exception, defaults to "A binary operator is not present in the list of operations"
    :type message: str, optional
    """
    def __init__(
        self, message="A binary operator is not present in the list of operations"
    ):
        super().__init__(message)


class InvalidKPINameException(Exception):
    """
    Exception raised when an invalid KPI name is encountered.

    :param message: The error message to be associated with the exception, defaults to "Invalid KPI name"
    :type message: str, optional
    """

    def __init__(self, message="Invalid KPI name"):
        super().__init__(message)


class KPIFormulaNotFoundException(Exception):
    """Exception raised when a KPI formula cannot be found.

    :param message: The error message to be associated with the exception, defaults to "KPI formula not found"
    :type message: str, optional
    """
    def __init__(self, message="KPI formula not found"):
        super().__init__(message)
