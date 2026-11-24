import unittest

import agent_team


class ManagerFallbackTests(unittest.TestCase):
    def test_fallback_preserves_each_role_once_and_all_headings(self):
        outputs = {
            "Research Analyst": "Research claim.\n\nInsight: Research claim; filing.txt, line 10.",
            "Financial Analyst": "Financial claim.\n\nInsight: Financial claim; filing.txt, line 20.",
            "Investment Advisor": "Advisor claim.\n\nInsight: Advisor claim; filing.txt, line 30.",
        }

        report, checks = agent_team.deterministic_manager_report(outputs)

        for output in outputs.values():
            self.assertEqual(report.count(output), 1)
        for heading in (
            "## Overview",
            "## Market Positioning and Growth Outlook",
            "## Valuation Insights",
            "## Future Developments and Strategic Recommendations",
            "## Investment Recommendation",
        ):
            self.assertIn(heading, report)
        self.assertTrue(all(item["status"] == "pass" for item in checks))

    def test_fallback_text_is_valid_input_to_report_parser(self):
        outputs = {
            "Research Analyst": "Research.\n\nInsight: Research; filing.txt, line 10.",
            "Financial Analyst": "Financial.\n\nInsight: Financial; filing.txt, line 20.",
            "Investment Advisor": "Advisor.\n\nInsight: Advisor; filing.txt, line 30.",
        }
        report, _checks = agent_team.deterministic_manager_report(outputs)
        self.assertEqual(report.count("Insight:"), 3)

    def test_exact_fact_evidence_controls_model_scale_error(self):
        items = [{
            "id": "C001",
            "text": "Revenue: $402,836 million.",
            "code_mark": None,
            "code_checks": ["Exact XBRL tag, period, accession, value, and unit match."],
            "facts": [{"val": 402_836_000_000, "unit": "USD"}],
            "correction": "",
        }]
        model = {"items": [{"id": "C001", "mark": "wrong", "reason": "Scale mismatch."}]}
        rows = agent_team.mark_rows(items, model)
        self.assertEqual(rows[0]["mark"], "correct")
        self.assertIn("deterministic exact-fact evidence controls", rows[0]["reason"])


if __name__ == "__main__":
    unittest.main()
