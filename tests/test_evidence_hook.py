import json
import tempfile
import unittest
from pathlib import Path

from evidence_hook import check_report


class EvidenceHookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self.temp.name)
        self.facts = {
            "total_revenue": {
                "tag": "RevenueFromContractWithCustomerExcludingAssessedTax",
                "val": 100000000,
                "prior_val": 90000000,
                "unit": "USD",
                "end": "2026-12-31",
                "fy": 2026,
                "accn": "0000000000-26-000001",
            },
            "period_end": {"end": "2026-12-31", "prior_end": "2025-12-31"},
        }
        (self.run_dir / "facts.json").write_text(json.dumps(self.facts), encoding="utf-8")
        (self.run_dir / "filings.json").write_text(
            json.dumps({"10-K": {"date": "2027-02-01", "accession": "0000000000-26-000001"}}),
            encoding="utf-8",
        )
        (self.run_dir / "10-K_2027-02-01.txt").write_text(
            "Revenue was 100 million for fiscal 2026.\n", encoding="utf-8"
        )

    def tearDown(self):
        self.temp.cleanup()

    def check(self, amount: str) -> dict:
        report = self.run_dir / "report.md"
        report.write_text(
            "Filings read: 10-K accession 0000000000-26-000001\n\n"
            f"Revenue was ${amount} million in FY2026; tag `RevenueFromContractWithCustomerExcludingAssessedTax`; "
            "period end 2026-12-31 (10-K, line 1).\n",
            encoding="utf-8",
        )
        return check_report(report, self.run_dir)

    def test_correct_xbrl_value_passes(self):
        result = self.check("100")
        self.assertEqual(result["refused"], 0)
        self.assertEqual(result["passed"], 1)

    def test_changed_xbrl_value_is_refused(self):
        result = self.check("101")
        self.assertEqual(result["refused"], 1)

    def test_number_without_source_is_refused(self):
        report = self.run_dir / "report.md"
        report.write_text("Filings read: none\n\nRevenue was $100 million.\n", encoding="utf-8")
        result = check_report(report, self.run_dir)
        self.assertEqual(result["refused"], 1)


if __name__ == "__main__":
    unittest.main()
