import unittest
from pathlib import Path

import source_report


class SourceReportTests(unittest.TestCase):
    def test_find_fact_line_prefers_label_and_value(self) -> None:
        lines = [
            "Other line with 402,836",
            "Total revenues | $ | 350,018 | $ | 402,836 |",
        ]
        fact = {"val": 402_836_000_000, "unit": "USD"}
        self.assertEqual(source_report.find_fact_line(lines, "total_revenue", fact), 2)

    def test_value_format_preserves_current_debt_scale(self) -> None:
        fact = {"val": 1_996_000_000, "unit": "USD"}
        self.assertEqual(source_report._display_value(fact), "$1,996 million")

    def test_current_debt_line_can_use_value_when_label_is_separate(self) -> None:
        lines = ["Current portion of long-term debt", "| ( 999 ) | ( 1,996 ) |"]
        fact = {"val": 1_996_000_000, "unit": "USD"}
        self.assertEqual(source_report.find_fact_line(lines, "current_debt", fact), 2)

    def test_direct_fact_insight_does_not_need_ratio_arithmetic(self) -> None:
        claim = "Revenue: $402,836 million; tag `Revenues`."
        insight = claim.replace("Revenue:", "Insight: Revenue was")
        self.assertEqual(insight, "Insight: Revenue was $402,836 million; tag `Revenues`.")

    def test_fact_claim_has_one_value_and_one_period(self) -> None:
        fact = {
            "val": 129_039_000_000,
            "prior_val": 112_390_000_000,
            "unit": "USD",
            "tag": "OperatingIncomeLoss",
            "end": "2025-12-31",
        }
        claim = source_report._fact_claim(
            "operating_income", "Operating income", fact, "10-K.txt", 650, "0001"
        )
        self.assertIn("$129,039 million", claim)
        self.assertNotIn("112,390", claim)
        self.assertEqual(claim.count("period end"), 1)
        self.assertIn("Form 10-K accession 0001", claim)
        self.assertNotIn("line 650", claim)


if __name__ == "__main__":
    unittest.main()
