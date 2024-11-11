import unittest
from datetime import datetime
from src.main.app.services.kpi_request import KPIRequest


class TestKPIRequest(unittest.TestCase):
    def setUp(self):
        self.valid_name = "Efficiency"
        self.valid_machine = "Machine_1"
        self.valid_aggregation = "mean"
        self.valid_start_date = datetime(2023, 1, 1)
        self.valid_end_date = datetime(2023, 12, 31)

        self.kpi_request = KPIRequest(
            self.valid_name,
            self.valid_machine,
            self.valid_aggregation,
            self.valid_start_date,
            self.valid_end_date,
        )

    def test_initialization(self):
        self.assertEqual(self.kpi_request.name, self.valid_name)
        self.assertEqual(self.kpi_request.machine, self.valid_machine)
        self.assertEqual(self.kpi_request.aggregation, self.valid_aggregation)
        self.assertEqual(self.kpi_request.start_date, self.valid_start_date)
        self.assertEqual(self.kpi_request.end_date, self.valid_end_date)

    def test_name_setter_valid(self):
        self.kpi_request.name = "Performance"
        self.assertEqual(self.kpi_request.name, "Performance")

    def test_name_setter_invalid(self):
        with self.assertRaises(ValueError):
            self.kpi_request.name = 123  # Non-string type

    def test_machine_setter_valid(self):
        self.kpi_request.machine = "Machine_2"
        self.assertEqual(self.kpi_request.machine, "Machine_2")

    def test_machine_setter_invalid(self):
        with self.assertRaises(ValueError):
            self.kpi_request.machine = 456  # Non-string type

    def test_aggregation_setter_valid(self):
        self.kpi_request.aggregation = "sum"
        self.assertEqual(self.kpi_request.aggregation, "sum")

    def test_aggregation_setter_invalid_type(self):
        with self.assertRaises(ValueError):
            self.kpi_request.aggregation = 789  # Non-string type

    def test_aggregation_setter_invalid_agg(self):
        with self.assertRaises(ValueError):
            self.kpi_request.aggregation = "SUM"  # Non-string type

    def test_start_date_setter_valid(self):
        # Test setting a valid start date
        new_start_date = datetime(2023, 6, 1)
        self.kpi_request.start_date = new_start_date
        self.assertEqual(self.kpi_request.start_date, new_start_date)

    def test_start_date_setter_invalid(self):
        # Test setting an invalid start date (non-datetime)
        with self.assertRaises(ValueError):
            self.kpi_request.start_date = "2023-06-01"  # Non-datetime type

    def test_end_date_setter_valid(self):
        # Test setting a valid end date
        new_end_date = datetime(2023, 12, 1)
        self.kpi_request.end_date = new_end_date
        self.assertEqual(self.kpi_request.end_date, new_end_date)

    def test_end_date_setter_invalid(self):
        # Test setting an invalid end date (non-datetime)
        with self.assertRaises(ValueError):
            self.kpi_request.end_date = "2023-12-01"  # Non-datetime type


if __name__ == "__main__":
    unittest.main()
