"""Build a source-backed correction without changing saved filings or facts."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import desk_app


FACT_ORDER = (
    ("total_revenue", "Revenue"),
    ("operating_income", "Operating income"),
    ("net_income", "Net income"),
    ("diluted_eps", "Diluted EPS"),
    ("equity", "Stockholders' equity"),
    ("current_debt", "Current long-term debt"),
    ("long_term_debt", "Noncurrent long-term debt"),
    ("cash_from_operations", "Cash from operations"),
    ("capex", "Capital spending"),
    ("depreciation", "Depreciation"),
    ("diluted_shares", "Diluted shares"),
)

LABEL_HINTS = {
    "total_revenue": ("total revenue", "net sales"),
    "operating_income": ("operating income",),
    "net_income": ("net income",),
    "diluted_eps": ("diluted net income per share", "diluted earnings per share"),
    "equity": ("stockholders’ equity", "stockholders' equity", "total equity"),
    "current_debt": ("current portion",),
    "long_term_debt": ("long-term debt", "long term debt"),
    "cash_from_operations": ("net cash provided by operating activities",),
    "capex": ("purchases of property and equipment", "additions to property and equipment"),
    "depreciation": ("depreciation of property and equipment", "depreciation"),
    "diluted_shares": ("number of shares used in per share computation", "diluted shares"),
}


def _prior_end(end: str) -> str:
    parsed = date.fromisoformat(end)
    return parsed.replace(year=parsed.year - 1).isoformat()


def _display_value(fact: dict[str, Any]) -> str:
    value = float(fact["val"])
    unit = str(fact.get("unit", ""))
    if unit == "USD/shares":
        return f"${value:,.2f} per share"
    if unit == "shares":
        return f"{value / 1_000_000:,.0f} million shares"
    return f"${value / 1_000_000:,.0f} million"


def _number_tokens(fact: dict[str, Any]) -> tuple[str, ...]:
    value = float(fact["val"])
    if fact.get("unit") == "USD/shares":
        return (f"{value:,.2f}",)
    million = abs(value) / 1_000_000
    return (f"{million:,.0f}", f"{int(abs(value)):,}")


def find_fact_line(lines: list[str], concept: str, fact: dict[str, Any]) -> int:
    """Return the strongest saved 10-K line for one fact."""
    tokens = _number_tokens(fact)
    hints = LABEL_HINTS.get(concept, ())
    best: tuple[int, int] | None = None
    for index, line in enumerate(lines, 1):
        lower = line.lower()
        token_hits = sum(token in line for token in tokens)
        if not token_hits:
            continue
        hint_hits = sum(hint in lower for hint in hints)
        score = hint_hits * 10 + token_hits
        if best is None or score > best[0]:
            best = (score, index)
    if best is None:
        raise ValueError(f"No saved 10-K line contains {concept} value {fact.get('val')}")
    return best[1]


def _fact_claim(
    concept: str,
    label: str,
    fact: dict[str, Any],
    filename: str,
    line: int,
    accession: str,
) -> str:
    period = str(fact["end"])
    return (
        f"{label}: {_display_value(fact)}; tag `{fact['tag']}`; period end {period}; "
        f"Form 10-K accession {accession}."
    )


def _ratio_claims(
    facts: dict[str, Any], filename: str, lines: dict[str, int], accession: str
) -> list[str]:
    revenue = float(facts["total_revenue"]["val"])
    prior_revenue = float(facts["total_revenue"]["prior_val"])
    operating = float(facts["operating_income"]["val"])
    income = float(facts["net_income"]["val"])
    equity = float(facts["equity"]["val"])
    prior_equity = float(facts["equity"]["prior_val"])
    current_debt = float(facts["current_debt"]["val"])
    long_debt = float(facts["long_term_debt"]["val"])
    cfo = float(facts["cash_from_operations"]["val"])
    capex = abs(float(facts["capex"]["val"]))
    period = facts["total_revenue"]["end"]
    growth = (revenue - prior_revenue) / prior_revenue
    margin = operating / revenue
    roe = income / ((equity + prior_equity) / 2)
    debt_equity = (current_debt + long_debt) / equity
    free_cash_flow = cfo - capex
    return [
        f"Revenue growth is current-year revenue minus prior-year revenue, divided by prior-year revenue: "
        f"({int(revenue)} - {int(prior_revenue)}) / {int(prior_revenue)} = {growth:.4%}. "
        f"Tag `Revenues`; period end {period}; {filename}, line {lines['total_revenue']}; accession {accession}.",
        f"Operating margin is operating income divided by revenue: {int(operating)} / {int(revenue)} = {margin:.4%}. "
        f"Tags `OperatingIncomeLoss` and `Revenues`; period end {period}; {filename}, lines "
        f"{lines['operating_income']} and {lines['total_revenue']}; accession {accession}.",
        f"Return on average equity is net income divided by average beginning and ending equity: "
        f"{int(income)} / (({int(equity)} + {int(prior_equity)}) / 2) = {roe:.4%}. "
        f"Tags `NetIncomeLoss` and `StockholdersEquity`; period end {period}; {filename}, lines "
        f"{lines['net_income']} and {lines['equity']}; accession {accession}.",
        f"Debt to equity is current plus noncurrent long-term debt divided by ending equity: "
        f"({int(current_debt)} + {int(long_debt)}) / {int(equity)} = {debt_equity:.4%}. "
        f"Tags `LongTermDebtCurrent`, `LongTermDebtNoncurrent`, and `StockholdersEquity`; period end {period}; "
        f"{filename}, lines {lines['current_debt']}, {lines['long_term_debt']}, and {lines['equity']}; accession {accession}.",
        f"Free cash flow is cash from operations minus capital spending: {int(cfo)} - {int(capex)} = {int(free_cash_flow)}. "
        f"Tags `NetCashProvidedByUsedInOperatingActivities` and `PaymentsToAcquirePropertyPlantAndEquipment`; "
        f"period end {period}; {filename}, lines {lines['cash_from_operations']} and {lines['capex']}; accession {accession}.",
    ]


def build_source_report(run_dir: Path, ticker: str, peers: list[str]) -> str:
    """Build a minimal report whose claims can be recomputed from saved evidence."""
    facts = desk_app.read_json(run_dir / "facts.json")
    filings = desk_app.read_json(run_dir / "filings.json")
    metadata = desk_app.read_json(run_dir / "run_metadata.json")
    ten_k = run_dir / f"10-K_{filings['10-K']['date']}.txt"
    ten_k_lines = ten_k.read_text(encoding="utf-8", errors="replace").splitlines()
    fact_lines = {
        concept: find_fact_line(ten_k_lines, concept, facts[concept])
        for concept, _label in FACT_ORDER
    }
    accession = filings["10-K"]["accession"]
    header = desk_app.filing_header(ticker, filings, peers, run_dir)
    claims = [
        _fact_claim(concept, label, facts[concept], ten_k.name, fact_lines[concept], accession)
        for concept, label in FACT_ORDER
    ]
    equity_claim = claims[4].replace("Stockholders' equity:", "Insight: Stockholders' equity was")
    revenue_insight = claims[0].replace("Revenue:", "Insight: Revenue was")
    debt_insight = claims[6].replace(
        "Noncurrent long-term debt:", "Insight: Noncurrent long-term debt was"
    )
    worksheet_result = json.loads((run_dir / "worksheet_calculations.json").read_text(encoding="utf-8"))
    decision = worksheet_result["quantitative_decision"]
    recommendation = str(decision["rating"])
    body = [
        header,
        f"Run time: {metadata.get('run_time', 'not recorded')}",
        "",
        "## Overview",
        "",
        "The original model report and its refusal remain saved as `report.md` and `team_hook_marks.json`. "
        "This correction contains only saved filing facts and printed calculations.",
        "",
        "## Market Positioning and Growth Outlook",
        "",
        "No unsupported qualitative claim is added in this correction.",
        "",
        equity_claim,
        "",
        "## Valuation Insights",
        "",
        *claims,
    ]
    body.extend([
        "",
        revenue_insight,
        "",
        "## Future Developments and Strategic Recommendations",
        "",
        "No unsupported forecast or catalyst is added in this correction.",
        "",
        "## Investment Recommendation",
        "",
        f"The deterministic worksheet screen returns **{recommendation}**. Its inputs, arithmetic, value cases, "
        "and price comparison remain visible in `worksheet_output.md` and `worksheet_calculations.json`.",
        "",
        "Screens to look at, not a recommendation.",
        "",
        debt_insight,
        "",
    ])
    return "\n".join(body)


def write_source_report(run_dir: Path, ticker: str, peers: list[str]) -> Path:
    target = run_dir / "source_corrected_report.md"
    target.write_text(build_source_report(run_dir, ticker, peers), encoding="utf-8")
    return target
