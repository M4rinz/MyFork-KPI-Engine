import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import pandas as pd
from src.app.kpi_engine.kpi_engine import KPIEngine, InvalidKPINameException
from src.app.kpi_engine.kpi_request import KPIRequest
from src.app.kpi_engine.kpi_response import KPIResponse
from sqlalchemy.orm import Session


class TestKPIEngine(unittest.TestCase):
    def setUp(self):
        self.mock_dataframe = pd.DataFrame(
            {
                "kpi": ["A", "B", "A", "B"],
                "time": [
                    datetime(2023, 1, 1),
                    datetime(2023, 1, 1),
                    datetime(2023, 1, 2),
                    datetime(2023, 1, 2),
                ],
                "value": [1, 2, 3, 4],
            }
        )
        self.request = KPIRequest(
            name="test_kpi",
            machine="machine1",
            aggregation="sum",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
        )
        self.aggregations = ["sum", "mean", "max", "min", "std", "var"]
        self.expected_results = [10.0, 5.0, 7.0, 3.0, 2.0, 4.0]

    @patch("src.app.kpi_engine.kpi_engine.get_kpi_formula")
    @patch("pandas.read_sql")
    @patch("sqlalchemy.orm.Session.query")
    def test_compute_valid_kpi(self, mock_query, mock_read_sql, mock_get_kpi_formula):
        for aggregation, expected_result in zip(
            self.aggregations, self.expected_results
        ):
            with self.subTest(aggregation=aggregation):
                # Mock the response for get_kpi_formula
                mock_get_kpi_formula.return_value = "A + B"

                # Create a mock query object to chain the query calls
                mock_filter = MagicMock()
                mock_with_entities = MagicMock()
                mock_statement = "mock_statement"

                # Set up the mock chain for query -> filter -> with_entities -> statement
                mock_query.return_value = mock_filter
                mock_filter.filter.return_value = mock_with_entities
                mock_with_entities.with_entities.return_value = mock_with_entities
                mock_with_entities.statement = mock_statement

                # Simulate the DataFrame that would be returned by read_sql
                mock_read_sql.return_value = self.mock_dataframe

                # Mock the 'bind' attribute of the Session to return the mock connection
                mock_DB = MagicMock(spec=Session)
                mock_DB.bind = "mock_bind"

                self.request.aggregation = aggregation

                result = KPIEngine.compute(
                    db=mock_DB,
                    details=self.request,
                )

                self.assertIsInstance(result, KPIResponse)
                self.assertEqual(
                    result.message,
                    f"The {aggregation} of KPI {self.request.name} for "
                    f"{self.request.machine} from {self.request.start_date} to "
                    f"{self.request.end_date} is {expected_result}",
                )
                self.assertEqual(result.value, expected_result)

    @patch("src.app.kpi_engine.kpi_engine.get_kpi_formula")
    @patch("pandas.read_sql")
    def test_compute_invalid_kpi(self, mock_read_sql, mock_get_kpi_formula):
        # Mock the response for get_kpi_formula to return None (invalid KPI)
        mock_get_kpi_formula.return_value = None

        # Setup the test input details (KPIRequest)
        details = KPIRequest(
            name="invalid_kpi",
            machine="machine1",
            aggregation="sum",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
        )

        # Simulate the `compute` method
        result = KPIEngine.compute(
            db=MagicMock(spec=Session),  # Mock the real-time data session
            details=details,
        )

        # Verify that the formula fetch failed as expected
        mock_get_kpi_formula.assert_called_once_with("invalid_kpi", "machine1")

        # Test that the result is an error message
        self.assertIsInstance(result, KPIResponse)
        self.assertEqual(result.message, "Invalid KPI name or machine")
        self.assertEqual(result.value, -1)

    @patch("requests.get")
    def test_invalid_kpi_formula(self, mock_requests_get):
        mock_requests_get.side_effect = InvalidKPINameException()

        self.assertRaises(
            InvalidKPINameException,
            KPIEngine.compute,
            MagicMock(spec=Session),
            self.request,
        )


if __name__ == "__main__":
    unittest.main()
