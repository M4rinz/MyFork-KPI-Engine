import unittest
from unittest.mock import patch
from datetime import datetime
from src.main.app.services.kpi_engine import KPIEngine, KPIRequest


class TestKPIEngine(unittest.TestCase):
    @patch("src.main.app.services.kpi_engine.get_kpi_formula")
    @patch("src.main.app.services.kpi_engine.BaseKPI.objects.filter")
    def test_compute_valid_kpi(self, mock_filter, mock_get_kpi_formula):
        # Setup
        mock_get_kpi_formula.return_value = "A + B"  # Mocking the formula

        # Mocking the filter and values method to return a list of records
        mock_filter.return_value.values.return_value = [
            {"name": "A", "value": 10, "timestamp": datetime(2024, 1, 1)},
            {"name": "B", "value": 5, "timestamp": datetime(2024, 1, 1)},
            {"name": "A", "value": 2, "timestamp": datetime(2024, 1, 2)},
            {"name": "B", "value": 3, "timestamp": datetime(2024, 1, 2)},
        ]

        # Prepare a KPIRequest with necessary details
        details = KPIRequest(
            name="C",
            machine="machine1",
            aggregation="sum",  # Let's assume we're using 'sum' as the aggregation
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 3),
        )

        # Call the compute function
        response = KPIEngine.compute(details)

        # Assert that the response is correct (mocking the result)
        self.assertEqual(response.name, "abc")
        self.assertEqual(response.value, 20)

        # Verify that the mocked methods were called correctly
        mock_get_kpi_formula.assert_called_once_with("C", "machine1")
        mock_filter.assert_called_once_with(
            name__in={"A", "B"},
            machine="machine1",
            timestamp__range=(datetime(2024, 1, 1), datetime(2024, 1, 2)),
        )

    @patch("mymodule.kpi_engine.get_kpi_formula")
    @patch("mymodule.kpi_engine.BaseKPI.objects.filter")
    def test_compute_invalid_kpi_name(self, mock_filter, mock_get_kpi_formula):
        # Setup
        mock_get_kpi_formula.return_value = None  # Return None for invalid KPI name

        # Prepare a KPIRequest with necessary details
        details = KPIRequest(
            name="Invalid_C",
            machine="machine1",
            aggregation="sum",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 2),
        )

        # Call the compute function
        response = KPIEngine.compute(details)

        # Assert the response for invalid KPI name
        self.assertEqual(response.message, "Invalid KPI name")
        self.assertEqual(response.value, -1)

        # Verify that the mocked methods were called
        mock_get_kpi_formula.assert_called_once_with("invalid_kpi_name", "machine_1")
        mock_filter.assert_not_called()


if __name__ == "__main__":
    unittest.main()
