import unittest
from unittest.mock import MagicMock, patch

import numpy as np
import random
from src.app.kpi_engine.dynamic_calc import A, S, R, D, C, finalize_mo, keys_involved
from src.app.kpi_engine.exceptions import InvalidFormulaReferenceException


class TestFunctions(unittest.TestCase):
    def setUp(self):
        self.partial_result = {
            "agg_outer_vars": "mo",
            "agg": "mean",
        }
        self.formulas_dict = {
            "success_rate": "A°sum°mo[ S°*[S°/[ R°good_cycles_sum°T°m°o° ; R°cycles_sum°T°m°o° ] ; C°100°]]",
            "good_cycles_sum": "A°sum°mo[ A°sum°t[ D°good_cycles_sum°t°m°o° ]]",
            "cycles_sum": "A°sum°mo[ A°sum°t[ D°cycles_sum°t°m°o° ]]",
        }
        self.engine = MagicMock()
        self.request = MagicMock()

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

    @patch("src.app.kpi_engine.dynamic_calc.query_DB")
    def test_R(self, mock_query_DB):
        mock_query_DB.return_value = (np.zeros((2, 2)), None)

        result = R(
            "R°good_cycles_sum°T°m°o°",
            self.partial_result,
            self.formulas_dict,
            self.engine,
            self.request,
        )
        self.assertLessEqual(int(result[1:]), 100)
        self.assertGreaterEqual(int(result[1:]), 1)

        with self.assertRaises(InvalidFormulaReferenceException):
            R(
                "R°mock°T°m°o°",
                self.partial_result,
                self.formulas_dict,
                self.engine,
                self.request,
            )

    @patch("src.app.kpi_engine.dynamic_calc.query_DB")
    def test_D(self, mock_query_DB):
        mock_query_DB.return_value = (np.array([[1, 2], [3, 4]]), np.array([[5, 6]]))
        random.seed(1)
        result = D("kpi°test_query", self.partial_result, self.engine, self.request)

        self.assertTrue(result.startswith("°"))
        key = result[1:]
        self.assertIn(key, self.partial_result)
        self.assertEqual(self.partial_result[key], mock_query_DB.return_value)

    def test_C(self):
        random.seed(1)
        result = C("C°100°", self.partial_result)
        self.assertTrue(result.startswith("°"))
        self.assertTrue(1 <= int(result[1:]) <= 100)
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


if __name__ == "__main__":
    unittest.main()
