import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.app.kpi_engine.kpi_engine import KPIEngine
from src.app.kpi_engine.kpi_request import KPIRequest
from src.app.kpi_engine.kpi_response import KPIResponse
from src.app.kpi_engine.exceptions import InvalidKPINameException
from sqlalchemy.orm import Session
import KB.kb_interface as kbi


class TestKPIEngine(unittest.TestCase):
    def setUp(self):
        self.request = KPIRequest(
            name="power_cumulative",
            machines=["machine1", "machine2"],
            operations=["operation1", "operation2"],
            time_aggregation="sum",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            step=7,
        )
        self.aggregations = ["sum", "mean", "max", "min", "std", "var"]
        self.expected_results = [10.0, 5.0, 7.0, 3.0, 2.0, 4.0]
        kbi.start()
        self.db = MagicMock(spec=Session)

    # @patch("src.app.kpi_engine.kpi_engine.get_kpi_formula")
    # @patch("pandas.read_sql")
    # @patch("sqlalchemy.orm.Session.query")
    def test_compute_valid_kpi(self):
        for aggregation, expected_result in zip(
            self.aggregations, self.expected_results
        ):
            with self.subTest(aggregation=aggregation):
                # Mock the response for get_kpi_formula
                # mock_get_kpi_formula.return_value = "A + B"

                self.request.time_aggregation = aggregation

                result = KPIEngine.compute(
                    connection=self.db,
                    request=self.request,
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
            request=details,
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
