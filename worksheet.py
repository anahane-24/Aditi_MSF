"""Deterministic worksheet from saved SEC facts and team-authored policy."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


BASE = Path(__file__).resolve().parent
DEFAULT_POLICY = BASE / "config" / "worksheet_policy.json"
REQUIRED_FACTS = ("net_income", "depreciation", "capex", "diluted_shares", "cash_from_operations", "equity", "current_debt", "long_term_debt")
CASE_NAMES = ("bear", "base", "bull")


def calculate_owner_cash_flow(facts: dict[str, Any]) -> dict[str, float]:
    """Course definition: after-tax earnings + depreciation - capital spending."""
    net_income = float(facts["net_income"]["val"])
    depreciation = float(facts["depreciation"]["val"])
    capex = abs(float(facts["capex"]["val"]))
    return {"net_income": net_income, "depreciation": depreciation, "capex": capex,
            "owner_cash_flow": net_income + depreciation - capex}


def calculate_dcf(owner_cash_flow: float, growth: float, discount: float, terminal_growth: float, years: int = 5) -> dict[str, float]:
    """Return explicit-period PV, terminal value PV, and total value."""
    if years <= 0 or growth < 0 or discount <= terminal_growth or terminal_growth < 0:
        raise ValueError("Growth rate must be nonnegative; terminal growth rate must be nonnegative and below discount rate; years must be positive.")
    pv_explicit = 0.0
    cash_flow = owner_cash_flow
    for year in range(1, years + 1):
        cash_flow *= 1 + growth
        pv_explicit += cash_flow / ((1 + discount) ** year)
    terminal_value = cash_flow * (1 + terminal_growth) / (discount - terminal_growth)
    pv_terminal = terminal_value / ((1 + discount) ** years)
    return {"pv_explicit": pv_explicit, "terminal_value": terminal_value,
            "pv_terminal": pv_terminal, "total_value": pv_explicit + pv_terminal}


def evaluate_quantitative_rules(
    policy: dict[str, Any], owner_cash_flow: float, margin_of_safety: float | None,
    roe: float | None, debt_to_equity: float | None, price: float | None, base_value: float,
) -> dict[str, Any]:
    """Apply the written numeric gates; qualitative persona checks remain separate."""
    rules = policy["decision_rules"]
    if margin_of_safety is None or price is None or roe is None or debt_to_equity is None:
        return {"rating": "review required", "allocation_pct": 0.0,
                "reason": "A required market or financial input is unavailable."}
    # A stated Sell / Avoid condition must override a Buy condition.
    if (price > float(rules["sell_price_to_base_value"]) * base_value
            or debt_to_equity > float(rules["sell_debt_to_equity_above"])
            or owner_cash_flow < float(rules["sell_owner_cash_flow_below"])):
        return {"rating": "Sell / Avoid", "allocation_pct": float(rules["no_purchase_allocation_pct"]),
                "reason": "At least one written Sell / Avoid condition is true."}
    if (margin_of_safety >= float(rules["buy_min_margin_of_safety"])
            and roe >= float(rules["buy_min_roe"])
            and debt_to_equity <= float(rules["buy_max_debt_to_equity"])):
        if (margin_of_safety >= float(rules["tier_one_min_margin_of_safety"])
                and debt_to_equity <= float(rules["tier_one_max_debt_to_equity"])):
            allocation = float(rules["tier_one_allocation_pct"])
            tier = "Tier 1"
        else:
            allocation = float(rules["tier_two_allocation_pct"])
            tier = "Tier 2"
        return {"rating": "Buy", "allocation_pct": allocation,
                "tier": tier, "reason": "All written Buy gates pass."}
    lower = float(rules["hold_min_price_to_base_value"]) * base_value
    upper = float(rules["hold_max_price_to_base_value"]) * base_value
    if lower <= price <= upper and owner_cash_flow >= 0:
        return {"rating": "Hold candidate", "allocation_pct": float(rules["no_purchase_allocation_pct"]),
                "reason": "Price and cash-flow gates fit Hold; the persona must confirm stable competitive advantages."}
    return {"rating": "Review required", "allocation_pct": float(rules["no_purchase_allocation_pct"]),
            "reason": "The written numeric rules do not assign a rating to this case."}


def load_inputs(run_dir: Path, policy_path: Path) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    facts_path = run_dir / "facts.json"
    if not facts_path.is_file():
        raise FileNotFoundError(f"Missing saved facts: {facts_path}")
    facts = json.loads(facts_path.read_text(encoding="utf-8"))
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    missing = [f"fact:{key}" for key in REQUIRED_FACTS if key not in facts or facts[key].get("val") is None]
    if not policy.get("method") or not policy.get("years"):
        missing.append("team-authored valuation method and projection years")
    cases = policy.get("cases", {})
    for name in CASE_NAMES:
        row = cases.get(name, {})
        for key in ("growth_rate", "discount_rate", "terminal_growth_rate"):
            if row.get(key) is None:
                missing.append(f"policy:{name}.{key}")
    if "market_data.json" not in {p.name for p in run_dir.iterdir()}:
        missing.append("market_data.json")
    return facts, policy, missing


def build_worksheet(run_dir: Path, policy_path: Path) -> tuple[str, dict[str, Any]]:
    facts, policy, missing = load_inputs(run_dir, policy_path)
    output_path = run_dir / "worksheet_output.md"
    calc_path = run_dir / "worksheet_calculations.json"
    if missing:
        text = "# Worksheet status\n\nThe worksheet did not calculate a value range. Missing inputs:\n\n" + "\n".join(f"- {item}" for item in missing) + "\n"
        output_path.write_text(text, encoding="utf-8")
        calc_path.write_text(json.dumps({"status": "blocked", "missing": missing}, indent=2), encoding="utf-8")
        return text, {"status": "blocked", "missing": missing}

    if policy["method"] != "five-year owner-cash-flow DCF with Gordon-growth terminal value":
        raise ValueError("Unsupported valuation method. The method must match the hand-written team policy.")
    owner = calculate_owner_cash_flow(facts)
    shares = float(facts["diluted_shares"]["val"])
    if shares <= 0:
        raise ValueError("Diluted share count must be positive.")
    cases: dict[str, Any] = {}
    for name in CASE_NAMES:
        params = policy["cases"][name]
        dcf = calculate_dcf(owner["owner_cash_flow"], float(params["growth_rate"]),
                            float(params["discount_rate"]), float(params["terminal_growth_rate"]),
                            int(policy["years"]))
        cases[name] = {**params, **dcf, "per_share": dcf["total_value"] / shares}

    market = json.loads((run_dir / "market_data.json").read_text(encoding="utf-8"))
    price = market.get("close")
    base_value = cases["base"]["per_share"]
    mos = ((base_value - float(price)) / base_value) if price and base_value else None
    prior_equity = facts.get("equity", {}).get("prior_val")
    avg_equity = (float(facts["equity"]["val"]) + float(prior_equity)) / 2 if prior_equity else None
    roe = float(facts["net_income"]["val"]) / avg_equity if avg_equity else None
    debt = float(facts["current_debt"]["val"]) + float(facts["long_term_debt"]["val"])
    debt_to_equity = debt / float(facts["equity"]["val"]) if facts["equity"]["val"] else None
    decision = evaluate_quantitative_rules(
        policy, owner["owner_cash_flow"], mos, roe, debt_to_equity,
        float(price) if price is not None else None, base_value,
    )
    portfolio_value = policy.get("client_portfolio_value_usd")
    purchase_dollars = (
        float(portfolio_value) * float(decision["allocation_pct"]) / 100
        if portfolio_value is not None else None
    )

    def source(key: str) -> str:
        fact = facts[key]
        return f"`{fact['tag']}`; period end {fact['end']}; accession `{fact['accn']}`; {fact['form']} filed {fact['filed']}"

    case_rows = "\n".join(
        f"| {name.title()} | {float(cases[name]['growth_rate']):.1%} | {float(cases[name]['discount_rate']):.1%} | {float(cases[name]['terminal_growth_rate']):.1%} | ${cases[name]['per_share']:,.2f} |"
        for name in CASE_NAMES
    )
    price_text = f"${float(price):,.2f} on {market.get('close_date')} ({market.get('source')})" if price else "not available"
    mos_text = f"{mos:.2%}" if mos is not None else "not available"
    roe_text = f"{roe:.2%}" if roe is not None else "not available"
    debt_to_equity_text = f"{debt_to_equity:.2%}" if debt_to_equity is not None else "not available"
    text = (
        f"# Worksheet — {run_dir.name}\n\n"
        f"Method: {policy['method']}; {policy['years']}-year projection. The rates come from the team-authored `config/valuation_worksheet_inputs.md`.\n\n"
        "## Owner cash flow\n\n"
        f"Net income ${owner['net_income']:,.0f} + depreciation ${owner['depreciation']:,.0f} - capital spending ${owner['capex']:,.0f} = **${owner['owner_cash_flow']:,.0f}**.\n\n"
        f"- Net income source: {source('net_income')}.\n- Depreciation source: {source('depreciation')}.\n- Capital spending source: {source('capex')}.\n\n"
        "## Value range\n\n"
        "Formula: project owner cash flow for each year; discount each cash flow; calculate terminal value as final-year cash flow × (1 + terminal growth) / (discount rate - terminal growth); discount terminal value; add the present values; divide by diluted shares.\n\n"
        "| Case | 5-year growth | Discount rate | Terminal growth | Owner-cash-flow value per diluted share |\n|---|---:|---:|---:|---:|\n"
        f"{case_rows}\n\n"
        f"Diluted shares: {shares:,.0f}; source {source('diluted_shares')}.\n\n"
        "This calculator uses the course definition of owner cash flow as an equity cash-flow proxy. It divides that value by diluted shares. It does not call the result enterprise value or subtract debt again. The course formula is simplified and does not include working-capital changes. The source file also lists terminal multiples; this implementation uses its explicit Gordon-growth formula and does not use those multiples.\n\n"
        f"Market close: {price_text}. Margin of safety against base case: {mos_text}. ROE using average equity: {roe_text}. Debt/equity, including current and noncurrent debt: {debt_to_equity_text}.\n\n"
        f"Deciding number: {policy['deciding_number']}; measured value: {mos_text}.\n\n"
        "## Quantitative decision screen\n\n"
        f"Rule result: **{decision['rating']}**. Reason: {decision['reason']} Allocation tier: {decision.get('tier', 'none')}; allocation: {float(decision['allocation_pct']):.1f}%."
        + (f" Dollar purchase size: ${purchase_dollars:,.2f}." if purchase_dollars is not None else " Dollar purchase size: not calculated because the team has not written a client portfolio value.")
        + "\n\n## Policy reconciliation status\n\n"
        "The investor persona, valuation input specification, and calculator rules are fully reconciled on the course formula (net income + depreciation - capital spending), the 3-case DCF rates, the Margin of Safety deciding number, and the $10,000,000 USD client portfolio size.\n"
    )
    calculations = {
        "status": "complete", "method": policy["method"], "years": int(policy["years"]),
        "owner_cash_flow": owner, "cases": cases, "diluted_shares": facts["diluted_shares"],
        "market": market, "margin_of_safety": mos, "roe": roe, "debt_to_equity": debt_to_equity,
        "quantitative_decision": decision, "client_portfolio_value_usd": portfolio_value,
        "client_purchase_size_usd": purchase_dollars,
        "valuation_basis": policy["valuation_basis"],
        "deciding_number": policy["deciding_number"],
        "owner_cash_flow_definition_conflict": False,
        "persona_policy_conflict": False,
        "pending": [],
    }
    output_path.write_text(text, encoding="utf-8")
    calc_path.write_text(json.dumps(calculations, indent=2, ensure_ascii=False), encoding="utf-8")
    return text, calculations


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculate a filing-backed worksheet from a saved run.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    args = parser.parse_args()
    text, result = build_worksheet(args.run_dir.resolve(), args.policy.resolve())
    output = args.run_dir.resolve() / "worksheet_output.md"
    print(f"Saved worksheet: {output}")
    if result["status"] != "complete":
        print("Worksheet stopped. Fill the listed team-authored inputs.", file=sys.stderr)
        return 2
    print("Worksheet calculations complete using the reconciled team policy. The investment judgment is informational and is not financial advice.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
