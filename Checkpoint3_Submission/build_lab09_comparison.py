"""Build a source-linked Lab 09 comparison from saved GOOGL and MSFT runs."""

from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import evidence_hook

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).with_name("Lab09_GOOGL_MSFT_Comparison.md")
FACTS = [
    ("Revenue", "total_revenue", "revenue"),
    ("Operating income", "operating_income", "operating income"),
    ("Net income", "net_income", "net income"),
    ("Diluted EPS", "diluted_eps", "diluted EPS"),
    ("Stockholders' equity", "equity", "stockholders' equity"),
    ("Current debt", "current_debt", "current debt"),
    ("Long-term debt", "long_term_debt", "long-term debt"),
    ("Cash from operations", "cash_from_operations", "cash from operations"),
    ("Capital spending", "capex", "capital spending"),
    ("Depreciation", "depreciation", "depreciation"),
    ("Diluted shares", "diluted_shares", "diluted shares"),
]
LABELS = {
    "total_revenue": "Total revenue",
    "operating_income": "Operating income",
    "net_income": "Net income",
    "diluted_eps": "Diluted",
    "equity": "Total stockholders",
    "current_debt": "Current portion of long-term debt",
    "long_term_debt": "Long-term debt",
    "cash_from_operations": "Net cash from operations",
    "capex": "Additions to property and equipment",
    "depreciation": "Depreciation",
    "diluted_shares": "Weighted average shares outstanding",
}


def latest_run(prefix: str) -> Path:
    matches = sorted((ROOT / "data").glob(prefix + "*"), key=lambda path: path.name)
    if not matches:
        raise FileNotFoundError(f"No saved run for {prefix}")
    return matches[-1]


def excerpt(report: str, keyword: str) -> str:
    for line in report.splitlines():
        if keyword.casefold() in line.casefold():
            cleaned = " ".join(line.split())
            return cleaned[:200] + ("…" if len(cleaned) > 200 else "")
    return "Not stated in the individual model report."


def filing_line_reference(run: Path, key: str, fact: dict) -> str:
    filing = next(run.glob("10-K_*.txt"))
    lines = filing.read_text(encoding="utf-8", errors="replace").splitlines()
    if key == "depreciation":
        needle = f"{float(fact['val']) / 1_000_000_000:.1f} billion"
    elif key == "diluted_eps":
        needle = f"{float(fact['val']):.2f}"
    elif key == "diluted_shares":
        needle = f"{float(fact['val']) / 1_000_000:,.0f}"
    else:
        needle = f"{float(fact['val']) / 1_000_000:,.0f}"
    label = LABELS[key].casefold()
    matches = [i for i, line in enumerate(lines) if needle.casefold() in line.casefold()]
    candidates = []
    for value_idx in matches:
        prior_labels = [i for i in range(max(0, value_idx - 45), value_idx + 1) if label in lines[i].casefold()]
        if prior_labels:
            label_idx = prior_labels[-1]
            candidates.append((value_idx - label_idx, label_idx, value_idx))
    if not candidates:
        if matches:
            return f"{filing.name} line {matches[0] + 1} has the value token; partner must confirm the row context"
        return "Value line not matched automatically; partner must find it in the 10-K."
    _, start, end = min(candidates)
    return f"{filing.name} lines {start + 1}-{end + 1}"


def build_section(ticker: str, display_name: str, prefix: str) -> list[str]:
    run = latest_run(prefix)
    facts = json.loads((run / "facts.json").read_text(encoding="utf-8"))
    metadata = json.loads((run / "run_metadata.json").read_text(encoding="utf-8"))
    calculations = json.loads((run / "worksheet_calculations.json").read_text(encoding="utf-8"))
    report_path = run / "report.md"
    report = report_path.read_text(encoding="utf-8", errors="replace")
    joined = "# NOT VERIFIED — Lab 09 joined draft\n\nThe model report failed the evidence hook. This file preserves the model output and adds the deterministic worksheet. Do not submit it as a verified report.\n\n" + report + "\n\n## Worksheet\n\n" + (run / "worksheet_output.md").read_text(encoding="utf-8", errors="replace")
    joined_path = run / "joined_report.md"
    joined_path.write_text(joined, encoding="utf-8")
    hook_path = run / "team_hook_marks.json"
    if not hook_path.exists():
        hook_path = run / "evidence_hook_marks.json"
    hook = json.loads(hook_path.read_text(encoding="utf-8")) if hook_path.exists() else {}
    worksheet_hook = evidence_hook.check_worksheet(run)
    (run / "worksheet_hook_marks.json").write_text(json.dumps(worksheet_hook, indent=2), encoding="utf-8")

    lines = [
        f"## {display_name} ({ticker})",
        "",
        f"Run folder: `{run.relative_to(ROOT)}`. Filed time: `{metadata['filed_time_eastern']}`. Close: `${metadata['price']:.2f}` on `{metadata['price_date']}` from `{metadata['price_source']}`.",
        "",
        f"Individual report: `{(run / 'report.md').relative_to(ROOT)}`. Joined draft: `{joined_path.relative_to(ROOT)}`. The report hook marks the model report as **REFUSED** ({hook.get('passed', 0)} claims passed; {hook.get('refused', 'not recorded')} refused). The worksheet hook marks its calculations **{worksheet_hook['mark'].upper()}**. The joined draft is not verified.",
        "",
        "| Core claim | Individual report + worksheet | Joined report | Filing / saved facts |",
        "|---|---|---|---|",
    ]
    for label, key, term in FACTS:
        fact = facts[key]
        val = float(fact["val"])
        if key == "diluted_eps":
            value = f"${val:,.2f} per share"
        elif key == "diluted_shares":
            value = f"{val:,.0f} shares"
        else:
            value = f"${val:,.0f}"
        model_text = excerpt(report, term)
        worksheet_note = "Worksheet uses this fact." if key in {"net_income", "depreciation", "capex", "diluted_shares"} else "Worksheet does not calculate this fact."
        line_ref = filing_line_reference(run, key, fact)
        lines.append(
            f"| {label} | Model: {model_text}<br>Worksheet: {worksheet_note} | Same model claim is retained; worksheet adds its cited calculation where applicable. | {value}; tag `{fact['tag']}`; period end `{fact['end']}`; accession `{fact['accn']}`; {fact['form']} filed `{fact['filed']}`; line evidence: {line_ref}. |"
        )
    owner = calculations["owner_cash_flow"]["owner_cash_flow"]
    base = calculations["cases"]["base"]["per_share"]
    mos = calculations["margin_of_safety"]
    decision = calculations.get("quantitative_decision", {})
    purchase_size = calculations.get("client_purchase_size_usd")
    decision_text = decision.get("rating", "not calculated")
    allocation_text = f"{float(decision.get('allocation_pct', 0)):.1f}%"
    purchase_text = f"${float(purchase_size):,.2f}" if purchase_size is not None else "not calculated"
    lines.extend([
        f"| **View** | Model view is not accepted as verified; see report evidence-hook marks. The deterministic worksheet screen returns **{decision_text}** with {allocation_text} allocation ({purchase_text}). | Joined draft retains the unverified model view and includes the recalculated worksheet. The joined report remains unverified. | The worksheet hook checks sources and arithmetic. A passing worksheet does not clear the model-report refusal. |",
        f"| **Deciding number** | Worksheet computes owner cash flow ${owner:,.0f}, base-case owner-cash-flow value ${base:,.2f}/share, and Margin of Safety {mos:.2%}. | The worksheet applies the reconciled written policy. The model's investment thesis remains unverified. | Course formula: net income + depreciation - capital spending. The value is divided by diluted shares, with no second debt subtraction. Price comes from saved market data. |",
        "",
        "### Partner hand-check record — pending",
        "",
        "The partner must choose at least 2 claims, open the cited SEC filing, and enter their own marks and line references. Do not copy the AI hook result into this section.",
        "",
        "| Claim checked by partner | Filing and exact line checked | Partner mark (correct / wrong) | Partner initials and date |",
        "|---|---|---|---|",
        "| ____________________ | ____________________ | ____________________ | ____________________ |",
        "| ____________________ | ____________________ | ____________________ | ____________________ |",
        "",
    ])
    return lines


def main() -> None:
    output = [
        "# Lab 09 — GOOGL and MSFT comparison",
        "",
        "The partner selected Google and Microsoft. This file uses GOOGL for Google (Alphabet Inc., Class A). Confirm that ticker choice with the partner. The reports below are failed practice runs, not verified submissions.",
        "",
        "The saved runs were made on 2026-11-22. Both releases were accepted on 2026-10-28, which is within 30 days. These were not live views within 24 hours of filing.",
        "",
    ]
    output.extend(build_section("GOOGL", "Google / Alphabet Inc.", "Alphabet_Inc._20261122_"))
    output.extend(build_section("MSFT", "Microsoft Corporation", "MICROSOFT_CORP_20261122_"))
    OUT.write_text("\n".join(output), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
