import unittest

from worksheet import calculate_dcf, calculate_owner_cash_flow, evaluate_quantitative_rules


class WorksheetCalculationTests(unittest.TestCase):
    def setUp(self):
        self.policy = {
            "decision_rules": {
                "buy_min_margin_of_safety": .20, "buy_min_roe": .15,
                "buy_max_debt_to_equity": .75,
                "tier_one_min_margin_of_safety": .30, "tier_one_max_debt_to_equity": .50,
                "tier_one_allocation_pct": 5, "tier_two_allocation_pct": 2.5,
                "sell_price_to_base_value": 1.2, "sell_debt_to_equity_above": 1,
                "sell_owner_cash_flow_below": 0,
                "hold_min_price_to_base_value": .8, "hold_max_price_to_base_value": 1.2,
                "no_purchase_allocation_pct": 0,
            }
        }

    def test_owner_cash_flow_uses_net_income_plus_depreciation_less_capex(self):
        facts = {
            "net_income": {"val": 100},
            "depreciation": {"val": 20},
            "capex": {"val": -30},
        }
        self.assertEqual(calculate_owner_cash_flow(facts)["owner_cash_flow"], 90)

    def test_dcf_allows_explicit_growth_above_discount_rate(self):
        result = calculate_dcf(100, 0.10, 0.085, 0.03, 5)
        self.assertGreater(result["total_value"], 0)

    def test_dcf_has_explicit_and_terminal_values(self):
        result = calculate_dcf(100, 0.04, 0.10, 0.02, 5)
        self.assertGreater(result["pv_explicit"], 0)
        self.assertGreater(result["pv_terminal"], 0)
        self.assertAlmostEqual(result["total_value"], result["pv_explicit"] + result["pv_terminal"])

    def test_buy_tier_one_uses_five_percent(self):
        result = evaluate_quantitative_rules(self.policy, 100, .35, .16, .4, 65, 100)
        self.assertEqual(result["rating"], "Buy")
        self.assertEqual(result["tier"], "Tier 1")
        self.assertEqual(result["allocation_pct"], 5)

    def test_buy_tier_two_uses_two_point_five_percent(self):
        result = evaluate_quantitative_rules(self.policy, 100, .25, .16, .6, 75, 100)
        self.assertEqual(result["tier"], "Tier 2")
        self.assertEqual(result["allocation_pct"], 2.5)

    def test_sell_gate_sets_zero_allocation(self):
        result = evaluate_quantitative_rules(self.policy, 100, .1, .1, 1.1, 100, 100)
        self.assertEqual(result["rating"], "Sell / Avoid")
        self.assertEqual(result["allocation_pct"], 0)

    def test_sell_condition_overrides_buy_gates(self):
        result = evaluate_quantitative_rules(self.policy, -1, .35, .20, .4, 65, 100)
        self.assertEqual(result["rating"], "Sell / Avoid")
        self.assertEqual(result["allocation_pct"], 0)

    def test_hold_is_candidate_not_automatic_persona_decision(self):
        result = evaluate_quantitative_rules(self.policy, 100, .1, .1, .8, 100, 100)
        self.assertEqual(result["rating"], "Hold candidate")
        self.assertIn("persona must confirm", result["reason"])

    def test_missing_inputs_require_review(self):
        result = evaluate_quantitative_rules(self.policy, 100, None, .1, .8, 100, 100)
        self.assertEqual(result["rating"], "review required")
        self.assertEqual(result["allocation_pct"], 0)


if __name__ == "__main__":
    unittest.main()
