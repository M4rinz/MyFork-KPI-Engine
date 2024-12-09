import unittest
from unittest.mock import MagicMock, patch

import numpy as np
import random
from src.app.kpi_engine.dynamic.dynamic_engine import (
    A,
    S,
    R,
    D,
    C,
    finalize_mo,
    keys_involved,
    query_DB,
    dynamic_kpi,
)
from src.app.models.exceptions import (
    InvalidFormulaReferenceException,
    EmptyQueryException,
    InvalidBinaryOperatorException,
)


class TestFunctions(unittest.TestCase):
    def setUp(self):
        self.partial_result = {
            "agg_outer_vars": "mo",
            "agg": "mean",
        }
        self.request = MagicMock()
        self.formulas_dict = {
            "success_rate": "A°sum°mo[ S°*[S°/[ R°good_cycles_sum°T°m°o° ; R°cycles_sum°T°m°o° ] ; C°100°]]",
            "good_cycles_sum": "A°sum°mo[ A°sum°t[ D°good_cycles_sum°t°m°o° ]]",
            "cycles_sum": "A°sum°mo[ A°sum°t[ D°cycles_sum°t°m°o° ]]",
        }
        self.engine = MagicMock()
        self.request = MagicMock()

    @patch("src.app.kpi_engine.dynamic.dynamic_engine.query_DB")
    def test_dynamic_kpi(self, mock_query_DB):
        mock_query_DB.return_value = (np.array([[1, 2], [3, 4]]), None)
        result = dynamic_kpi(
            self.formulas_dict["success_rate"],
            self.formulas_dict,
            self.partial_result,
            self.request,
        )
        self.assertRegex(result, r"°\w{2}")

    def test_A(self):
        self.partial_result["key1"] = (np.array([[1, 2], [3, 4]]), None)
        result = A("A°sum°t°key1", self.partial_result)

        self.assertEqual(result, "°key1")
        np.testing.assert_array_equal(self.partial_result["key1"], [3, 7])

    def test_S(self):
        self.partial_result["key1"] = np.array([1, 2, 3])
        self.partial_result["key2"] = np.array([4, 5, 6])

        result = S("S°+°key1,°key2", self.partial_result)
        self.assertEqual(result, "°key1")
        np.testing.assert_array_equal(self.partial_result["key1"], [5, 7, 9])

        with self.assertRaises(InvalidBinaryOperatorException):
            S("S°%°key1,°key2", self.partial_result)

    @patch("src.app.kpi_engine.dynamic.dynamic_engine.query_DB")
    def test_R(self, mock_query_DB):
        mock_query_DB.return_value = (np.zeros((2, 2)), None)

        result = R(
            "R°good_cycles_sum°T°m°o°",
            self.partial_result,
            self.formulas_dict,
            self.request,
        )

        self.assertTrue(result.startswith("°"))
        self.assertTrue(result[1:] in self.partial_result)

        with self.assertRaises(InvalidFormulaReferenceException):
            R(
                "R°mock°T°m°o°",
                self.partial_result,
                self.formulas_dict,
                self.request,
            )

    @patch("src.app.kpi_engine.dynamic.dynamic_engine.query_DB")
    def test_D(self, mock_query_DB):
        mock_query_DB.return_value = (np.array([[1, 2], [3, 4]]), np.array([[5, 6]]))
        random.seed(1)
        result = D("kpi°test_query", self.partial_result, self.request)

        self.assertTrue(result.startswith("°"))
        key = result[1:]
        self.assertIn(key, self.partial_result)
        self.assertEqual(self.partial_result[key], mock_query_DB.return_value)

    def test_C(self):
        random.seed(1)
        result = C("C°100°", self.partial_result)
        self.assertTrue(result.startswith("°"))
        key = result[1:]
        self.assertIn(key, self.partial_result)
        self.assertEqual(self.partial_result[key], 100)

    def test_finalize_mo(self):
        self.partial_result["key1"] = np.array([[1, 2], [3, 4]])
        result = finalize_mo("°key1", self.partial_result, "mean")
        self.assertEqual(result, 2.5)

    def test_keys_involved(self):
        kpi = "S°+°key1,°key2"
        result = keys_involved(kpi, {"key1": "val1", "key2": "val2"})
        self.assertEqual(result, ["key1", "key2"])

        kpi = "A°sum°t°15"
        result = keys_involved(kpi, {"15": "val"})
        self.assertEqual(result, ["15"])


class TestQueryDB(unittest.TestCase):
    class MockResponse:
        def __init__(self, data, status_code):
            self.data = data
            self.status_code = status_code

        def json(self):
            return self.data

    def setUp(self):
        self.request = MagicMock()
        self.request.machines = ["machine_1", "machine_2"]
        self.request.operations = ["operation_1", "operation_2"]
        self.request.start_date = "2024-01-01"
        self.request.end_date = "2024-01-31"
        self.request.step = 1

        self.requests_return_value = self.MockResponse(
            data={
                "data": [
                    (1, "operation_1", "2024-01-01", 100),
                    (2, "operation_2", "2024-01-01", 200),
                    (1, "operation_1", "2024-01-02", 150),
                    (2, "operation_2", "2024-01-02", 250),
                ]
            },
            status_code=200,
        )

    @patch("src.app.kpi_engine.dynamic.dynamic_engine.requests.get")
    def test_valid_kpi_and_query(self, mock_get):
        kpi = "D°consumption_sum"

        mock_get.return_value = self.requests_return_value
        step_split, bottom = query_DB(kpi, self.request)

        self.assertEqual(step_split.shape, (2, 1, 2))
        self.assertIsNone(bottom)

    def test_invalid_kpi_reference(self):
        kpi = "D°consumptionsum°mo"
        with self.assertRaises(ValueError):
            query_DB(kpi, self.request)

    def test_invalid_kpi_format(self):
        kpi = "D°consumption"
        with self.assertRaises(ValueError):
            query_DB(kpi, self.request)

    @patch("src.app.kpi_engine.dynamic.dynamic_engine.requests.get")
    def test_empty_query_result(self, mock_get):
        mock_get.requests_return_value = self.MockResponse(
            data={"data": []}, status_code=200
        )
        kpi = "D°consumption_sum"
        with self.assertRaises(EmptyQueryException):
            query_DB(kpi, self.request)

    @patch("src.app.kpi_engine.dynamic.dynamic_engine.requests.get")
    def test_step_split_with_remainder(self, mock_get):
        self.request.step = 3
        kpi = "D°consumption_sum"
        mock_get.return_value = self.requests_return_value
        step_split, bottom = query_DB(kpi, self.request)

        self.assertEqual(step_split.shape, (0, 3, 2))
        self.assertEqual(bottom.shape, (1, 2, 2))

    def test_invalid_kpi_with_no_match(self):
        kpi = "D°abc"
        with self.assertRaises(ValueError):
            query_DB(kpi, self.request)


if __name__ == "__main__":
    unittest.main()
