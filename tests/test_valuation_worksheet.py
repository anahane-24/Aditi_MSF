"""Unit tests for deterministic valuation worksheet."""

import unittest
from valuation_worksheet import calculate_dcf, run_valuation, format_markdown


class ValuationWorksheetTests(unittest.TestCase):
    def test_calculate_dcf_positive_value(self):
        val = calculate_dcf(ocf=100.0, growth_rate=0.05, discount_rate=0.10, terminal_growth=0.02, years=5)
        self.assertGreater(val, 100.0)

    def test_calculate_dcf_invalid_rates(self):
        with self.assertRaises(ValueError):
            calculate_dcf(ocf=100.0, growth_rate=0.05, discount_rate=0.02, terminal_growth=0.03)

    def test_run_valuation_buy_conviction(self):
        # Net income 9,226M, Depreciation 3,500M, Capex 6,435M -> Owner CF 6,291M
        # 444.4M shares -> Base IV
        # Low market price gives margin of safety > 20%
        res = run_valuation(
            net_income=9226.0,
            depreciation=3500.0,
            capex=6435.0,
            shares_outstanding=444.427,
            market_price=100.0,
            debt=6162.0,
            equity=35803.0,
            roe=0.284,
            portfolio_value=10_000_000.0,
        )
        self.assertEqual(res["owner_cash_flow"], 6291.0)
        self.assertGreater(res["margin_of_safety_pct"], 20.0)
        self.assertEqual(res["recommendation"], "Buy")
        self.assertIn(res["client_purchase_size_pct"], [2.5, 5.0])
        self.assertGreater(res["client_purchase_size_dollars"], 0.0)
        self.assertEqual(res["deciding_number"]["name"], "Margin of Safety Percentage against Base Case")

    def test_run_valuation_overvalued_sell_conviction(self):
        res = run_valuation(
            net_income=1000.0,
            depreciation=200.0,
            capex=800.0,
            shares_outstanding=100.0,
            market_price=200.0,
            debt=500.0,
            equity=1000.0,
            roe=0.10,
            portfolio_value=10_000_000.0,
        )
        self.assertEqual(res["recommendation"], "Sell / Avoid")
        self.assertEqual(res["client_purchase_size_pct"], 0.0)
        self.assertEqual(res["client_purchase_size_dollars"], 0.0)

    def test_negative_owner_cash_flow_overrides_otherwise_buy_eligible_case(self):
        res = run_valuation(
            net_income=1000.0,
            depreciation=100.0,
            capex=1200.0,
            shares_outstanding=100.0,
            market_price=1.0,
            debt=100.0,
            equity=1000.0,
            roe=0.20,
            portfolio_value=10_000_000.0,
        )
        self.assertEqual(res["recommendation"], "Sell / Avoid")
        self.assertEqual(res["client_purchase_size_pct"], 0.0)

    def test_price_exactly_twenty_percent_above_base_is_not_sell_gate(self):
        inputs = dict(
            net_income=1000.0,
            depreciation=500.0,
            capex=100.0,
            shares_outstanding=100.0,
            debt=100.0,
            equity=1000.0,
            roe=0.10,
            portfolio_value=10_000_000.0,
        )
        no_price = run_valuation(**inputs)
        exact_limit = run_valuation(**inputs, market_price=1.20 * no_price["base_intrinsic_value"])
        self.assertEqual(exact_limit["recommendation"], "Hold")

    def test_missing_market_price_does_not_create_hold_recommendation(self):
        res = run_valuation(
            net_income=1000.0,
            depreciation=500.0,
            capex=100.0,
            shares_outstanding=100.0,
            debt=100.0,
            equity=1000.0,
            roe=0.10,
        )
        self.assertEqual(res["recommendation"], "Review required")

    def test_format_markdown_includes_key_terms(self):
        res = run_valuation(
            net_income=9226.0,
            depreciation=3500.0,
            capex=6435.0,
            shares_outstanding=444.427,
            market_price=900.0,
            debt=6162.0,
            equity=35803.0,
            roe=0.284,
            portfolio_value=10_000_000.0,
        )
        md = format_markdown(res, "COST")
        self.assertIn("Owner Cash Flow", md)
        self.assertIn("Net Income + Depreciation - Capex", md)
        self.assertIn("Bear Case", md)
        self.assertIn("Base Case", md)
        self.assertIn("Bull Case", md)
        self.assertIn("Margin of Safety", md)
        self.assertIn("$10,000,000.00", md)


if __name__ == "__main__":
    unittest.main()
