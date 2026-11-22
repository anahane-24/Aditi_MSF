"""Unit tests for spinoff_seeker scoring on synthetic (made-up) data."""

import unittest
from spinoff_seeker import score_rows


class SpinoffSeekerTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "window_days": 90,
            "factors": [
                {
                    "name": "Post-distribution selling pressure window",
                    "field": "window_return",
                    "source_chapter": "Greenblatt Chapter 3",
                    "direction": "lower",
                    "threshold": 0.0,
                    "weight": 25.0,
                },
                {
                    "name": "Spinoff relative capitalization size",
                    "field": "relative_size_ratio",
                    "source_chapter": "Greenblatt Chapter 3",
                    "direction": "lower",
                    "threshold": 0.20,
                    "weight": 25.0,
                },
                {
                    "name": "Clean spinoff balance sheet leverage",
                    "field": "debt_to_equity",
                    "source_chapter": "Klarman Chapter 10",
                    "direction": "lower",
                    "threshold": 0.50,
                    "weight": 25.0,
                },
                {
                    "name": "Direct insider ownership and incentive alignment",
                    "field": "insider_ownership_pct",
                    "source_chapter": "Greenblatt Chapter 3",
                    "direction": "higher",
                    "threshold": 0.05,
                    "weight": 25.0,
                },
            ],
        }

    def test_candidate_meeting_all_factors_scores_100_points(self):
        candidate = {
            "filer": "Ideal Spinoff Corp",
            "features": {
                "window_return": -0.08,        # <= 0.0 -> meets factor (25 pts)
                "relative_size_ratio": 0.12,   # <= 0.20 -> meets factor (25 pts)
                "debt_to_equity": 0.35,        # <= 0.50 -> meets factor (25 pts)
                "insider_ownership_pct": 0.08, # >= 0.05 -> meets factor (25 pts)
            },
        }
        scored = score_rows([candidate], self.config)
        self.assertEqual(len(scored), 1)
        self.assertTrue(scored[0]["ranked"])
        self.assertEqual(scored[0]["total_points"], 100.0)
        self.assertIsNone(scored[0]["unranked_reason"])

    def test_candidate_failing_factors_scores_zero_points(self):
        candidate = {
            "filer": "Overpriced Leveraged Spinoff",
            "features": {
                "window_return": 0.25,         # > 0.0 -> fails (0 pts)
                "relative_size_ratio": 0.60,   # > 0.20 -> fails (0 pts)
                "debt_to_equity": 1.40,        # > 0.50 -> fails (0 pts)
                "insider_ownership_pct": 0.01, # < 0.05 -> fails (0 pts)
            },
        }
        scored = score_rows([candidate], self.config)
        self.assertEqual(len(scored), 1)
        self.assertTrue(scored[0]["ranked"])
        self.assertEqual(scored[0]["total_points"], 0.0)

    def test_missing_feature_marks_candidate_unranked(self):
        candidate = {
            "filer": "Incomplete Data Spinoff",
            "features": {
                "window_return": -0.05,
                "relative_size_ratio": 0.15,
                # debt_to_equity is missing!
                "insider_ownership_pct": 0.07,
            },
        }
        scored = score_rows([candidate], self.config)
        self.assertEqual(len(scored), 1)
        self.assertFalse(scored[0]["ranked"])
        self.assertIsNone(scored[0]["total_points"])
        self.assertIn("Clean spinoff balance sheet leverage", scored[0]["unranked_reason"])

    def test_empty_factors_raises_value_error(self):
        with self.assertRaises(ValueError):
            score_rows([{"filer": "X", "features": {}}], {"window_days": 90, "factors": []})

    def test_invalid_direction_raises_value_error(self):
        invalid_config = {
            "window_days": 90,
            "factors": [
                {
                    "name": "Bad Factor",
                    "field": "foo",
                    "source_chapter": "Test",
                    "direction": "upwards",
                    "threshold": 1.0,
                    "weight": 10.0,
                }
            ],
        }
        with self.assertRaises(ValueError):
            score_rows([{"filer": "X", "features": {"foo": 2.0}}], invalid_config)


if __name__ == "__main__":
    unittest.main()
