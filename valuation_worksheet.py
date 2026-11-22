"""Deterministic Valuation Worksheet engine for SEC equity research.

Calculates Owner Cash Flow (Course formula: Net Income + Depreciation - Capex),
3-case DCF intrinsic value range, margin of safety, client purchase size (percentage and dollars),
and conviction rating.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_PORTFOLIO_USD = 10_000_000.0


def calculate_dcf(ocf: float, growth_rate: float, discount_rate: float, terminal_growth: float, years: int = 5) -> float:
    """Calculate discounted cash flow present value with Gordon Growth terminal value."""
    if discount_rate <= terminal_growth:
        raise ValueError("Discount rate must be strictly greater than terminal growth rate.")
    pv_explicit = 0.0
    current_cf = ocf
    for t in range(1, years + 1):
        current_cf *= (1.0 + growth_rate)
        pv_explicit += current_cf / ((1.0 + discount_rate) ** t)
    terminal_cf = current_cf * (1.0 + terminal_growth)
    terminal_value = terminal_cf / (discount_rate - terminal_growth)
    pv_terminal = terminal_value / ((1.0 + discount_rate) ** years)
    return pv_explicit + pv_terminal


def run_valuation(
    net_income: float,
    depreciation: float,
    capex: float,
    shares_outstanding: float,
    market_price: float | None = None,
    debt: float = 0.0,
    equity: float = 1.0,
    roe: float = 0.20,
    portfolio_value: float = DEFAULT_PORTFOLIO_USD,
) -> dict[str, Any]:
    """Run deterministic valuation worksheet following course owner cash flow model: Net Income + Depreciation - Capex."""
    owner_cash_flow = net_income + depreciation - capex
    if shares_outstanding <= 0:
        raise ValueError("Shares outstanding must be positive.")

    # Parameter cases matching config/valuation_worksheet_inputs.md and config/worksheet_policy.json
    cases = {
        "bear": {"growth": 0.04, "discount": 0.10, "terminal_growth": 0.02},
        "base": {"growth": 0.07, "discount": 0.09, "terminal_growth": 0.025},
        "bull": {"growth": 0.10, "discount": 0.085, "terminal_growth": 0.03},
    }

    results: dict[str, Any] = {}
    for case_name, params in cases.items():
        total_val = calculate_dcf(
            owner_cash_flow,
            params["growth"],
            params["discount"],
            params["terminal_growth"],
        )
        iv_share = total_val / shares_outstanding
        results[case_name] = {
            "total_value": total_val,
            "intrinsic_value_per_share": iv_share,
            "parameters": params,
        }

    base_iv = results["base"]["intrinsic_value_per_share"]
    debt_to_equity = debt / equity if equity > 0 else 0.0

    margin_of_safety = None
    recommendation = "Review required"
    purchase_size_pct = 0.0
    purchase_size_dollars = 0.0
    deciding_number = None

    if market_price is not None and market_price > 0:
        margin_of_safety = (base_iv - market_price) / base_iv
        deciding_number = {
            "name": "Margin of Safety Percentage against Base Case",
            "value": margin_of_safety * 100.0,
            "unit": "percent",
            "formula": "(Base Intrinsic Value - Market Price) / Base Intrinsic Value",
        }

    # Apply mandatory Sell / Avoid conditions first. A strong margin of safety
    # cannot override negative owner cash flow or excessive leverage.
    if debt_to_equity > 1.0 or owner_cash_flow < 0 or (
        market_price is not None and market_price > 0 and market_price > 1.20 * base_iv
    ):
        recommendation = "Sell / Avoid"
        purchase_size_pct = 0.0
        purchase_size_dollars = 0.0
    elif market_price is not None and market_price > 0:
        # Conviction & purchase sizing logic matching calculator rules
        if margin_of_safety >= 0.20 and roe >= 0.15 and debt_to_equity <= 0.75:
            recommendation = "Buy"
            purchase_size_pct = 5.0 if (margin_of_safety >= 0.30 and debt_to_equity <= 0.50) else 2.5
        else:
            recommendation = "Hold"
            purchase_size_pct = 0.0

        purchase_size_dollars = portfolio_value * (purchase_size_pct / 100.0)

    return {
        "owner_cash_flow": owner_cash_flow,
        "net_income": net_income,
        "depreciation": depreciation,
        "capex": capex,
        "shares_outstanding": shares_outstanding,
        "market_price": market_price,
        "debt_to_equity": debt_to_equity,
        "roe": roe,
        "valuation_cases": results,
        "base_intrinsic_value": base_iv,
        "margin_of_safety_pct": margin_of_safety * 100.0 if margin_of_safety is not None else None,
        "recommendation": recommendation,
        "client_purchase_size_pct": purchase_size_pct,
        "client_purchase_size_dollars": purchase_size_dollars,
        "client_portfolio_value_usd": portfolio_value,
        "deciding_number": deciding_number,
    }


def format_markdown(data: dict[str, Any], ticker: str = "TARGET") -> str:
    """Format valuation worksheet as a publication-ready Markdown table."""
    cases = data["valuation_cases"]
    lines = [
        f"### Valuation Worksheet: Owner Cash Flow & Intrinsic Value ({ticker})",
        "",
        f"- **Net Income:** ${data['net_income']:,.2f} million",
        f"- **Depreciation:** ${data['depreciation']:,.2f} million",
        f"- **Capital Expenditures:** ${data['capex']:,.2f} million",
        f"- **Owner Cash Flow:** ${data['owner_cash_flow']:,.2f} million (`Net Income + Depreciation - Capex`)",
        f"- **Diluted Shares Outstanding:** {data['shares_outstanding']:,.2f} million",
        "",
        "| Valuation Case | 5-Year Growth | Discount Rate | Terminal Growth | Intrinsic Value / Share |",
        "|---|---|---|---|---:|",
        f"| **Bear Case** | {cases['bear']['parameters']['growth']*100:.1f}% | {cases['bear']['parameters']['discount']*100:.1f}% | {cases['bear']['parameters']['terminal_growth']*100:.1f}% | **${cases['bear']['intrinsic_value_per_share']:,.2f}** |",
        f"| **Base Case** | {cases['base']['parameters']['growth']*100:.1f}% | {cases['base']['parameters']['discount']*100:.1f}% | {cases['base']['parameters']['terminal_growth']*100:.1f}% | **${cases['base']['intrinsic_value_per_share']:,.2f}** |",
        f"| **Bull Case** | {cases['bull']['parameters']['growth']*100:.1f}% | {cases['bull']['parameters']['discount']*100:.1f}% | {cases['bull']['parameters']['terminal_growth']*100:.1f}% | **${cases['bull']['intrinsic_value_per_share']:,.2f}** |",
        "",
    ]
    if data.get("market_price") is not None:
        mos = data.get("margin_of_safety_pct")
        mos_str = f"{mos:.2f}%" if mos is not None else "N/A"
        dollars = data.get("client_purchase_size_dollars", 0.0)
        lines.extend([
            f"- **Current Market Price:** ${data['market_price']:,.2f}",
            f"- **Margin of Safety (Base Case):** {mos_str}",
            f"- **Conviction Recommendation:** **{data['recommendation']}**",
            f"- **Client Portfolio Value:** ${data['client_portfolio_value_usd']:,.2f}",
            f"- **Client Purchase Size Allocation:** **{data['client_purchase_size_pct']:.1f}%** (${dollars:,.2f} USD)",
            f"- **Deciding Number:** {data['deciding_number']['name']} = `{mos_str}`",
        ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic Valuation Worksheet for SEC Equity Research.")
    parser.add_argument("--net-income", type=float, required=True, help="Net income in millions")
    parser.add_argument("--depreciation", type=float, required=True, help="Depreciation in millions")
    parser.add_argument("--capex", type=float, required=True, help="Capital expenditures in millions")
    parser.add_argument("--shares", type=float, required=True, help="Diluted shares in millions")
    parser.add_argument("--price", type=float, default=None, help="Market price per share")
    parser.add_argument("--debt", type=float, default=0.0, help="Total debt in millions")
    parser.add_argument("--equity", type=float, default=1.0, help="Stockholders equity in millions")
    parser.add_argument("--roe", type=float, default=0.20, help="Return on equity")
    parser.add_argument("--portfolio", type=float, default=DEFAULT_PORTFOLIO_USD, help="Client portfolio size in USD")
    parser.add_argument("--ticker", default="EQUITY", help="Company ticker symbol")
    parser.add_argument("--out", type=Path, default=None, help="Output JSON path")
    args = parser.parse_args()

    res = run_valuation(
        net_income=args.net_income,
        depreciation=args.depreciation,
        capex=args.capex,
        shares_outstanding=args.shares,
        market_price=args.price,
        debt=args.debt,
        equity=args.equity,
        roe=args.roe,
        portfolio_value=args.portfolio,
    )
    md = format_markdown(res, args.ticker)
    print(md)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(res, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
