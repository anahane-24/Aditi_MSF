"""Deterministic output guard for saved desk reports.

The hook checks report claims against only the run's saved filings and facts.
It does not call a model. A model verifier can assess meaning separately.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import agent_team
import desk_app
import worksheet


def check_report(report_path: Path, run_dir: Path) -> dict[str, Any]:
    report = report_path.read_text(encoding="utf-8", errors="replace")
    # Verified reports place the verifier table before the compiled report.
    # Strip that table before scanning claims so the check does not count the
    # marks themselves as new financial claims.
    if "## Verifier table" in report and "\n---\n" in report:
        first = report.splitlines()[0] if report.splitlines() else "Filings read: unavailable"
        body = report.split("\n---\n", 1)[1]
        report = first + "\n\n" + body
    filings_path = run_dir / "filings.json"
    facts_path = run_dir / "facts.json"
    if not filings_path.is_file() or not facts_path.is_file():
        raise FileNotFoundError("Run folder must contain filings.json and facts.json")
    filings = desk_app.read_json(filings_path)
    items = agent_team.verifier_evidence(report, run_dir, filings)
    rows: list[dict[str, Any]] = []
    for item in items:
        text = item["text"]
        # The Investment Advisor's thesis and recommendation are deliberately
        # excluded by report_blocks; its sourced Insight line is still checked.
        numeric = bool(re.search(r"(?:\$|%|\b\d[\d,]*(?:\.\d+)?\s*(?:billion|million|bps|basis points)\b)", text, re.I))
        if not numeric and not text.lstrip().startswith("Insight:"):
            continue
        problems: list[str] = []
        if not item.get("sources") and not item.get("facts"):
            problems.append("No saved filing line or XBRL fact supports this claim.")
        if item.get("code_mark") in {"wrong", "unsupported"}:
            problems.extend(item.get("code_checks", []))
            if item.get("correction"):
                problems.append("Correction: " + item["correction"])

        for source in item.get("sources", []):
            if not source.get("valid"):
                problems.append(f"Cited line is missing or outside {source.get('filename', 'the saved filing')}.")
        arithmetic = item.get("arithmetic_check", "")
        if arithmetic and arithmetic.startswith("Arithmetic does not match"):
            problems.append(arithmetic)
        mark = "refused" if problems else "passed"
        rows.append({
            "id": item["id"],
            "mark": mark,
            "claim": text,
            "sources": item.get("sources", []),
            "facts": item.get("facts", []),
            "checks": problems or item.get("code_checks", []),
        })
    return {
        "report": str(report_path),
        "run_dir": str(run_dir),
        "claim_count": len(rows),
        "passed": sum(row["mark"] == "passed" for row in rows),
        "refused": sum(row["mark"] == "refused" for row in rows),
        "marks": rows,
    }


def check_verifier_marks(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "verification_marks.json"
    if not path.is_file():
        return {"mark": "refused", "checks": ["Verifier marks are missing."]}
    marks = json.loads(path.read_text(encoding="utf-8"))
    failed = [{"id": row.get("id"), "mark": row.get("mark"), "claim": row.get("claim", "")}
              for row in marks if row.get("mark") != "correct"]
    return {
        "mark": "refused" if failed else "passed",
        "checks": [f"{item['id']} is marked {item['mark']}: {item['claim'][:180]}" for item in failed]
        or ["All model-verifier marks are correct."],
    }


def check_worksheet(run_dir: Path) -> dict[str, Any]:
    """Recompute worksheet inputs and valuation from saved facts and policy."""
    calc_path = run_dir / "worksheet_calculations.json"
    report_path = run_dir / "worksheet_output.md"
    if not calc_path.is_file() or not report_path.is_file():
        return {"mark": "refused", "checks": ["Worksheet output or calculations file is missing."]}
    calculations = json.loads(calc_path.read_text(encoding="utf-8"))
    if calculations.get("status") != "complete":
        return {"mark": "refused", "checks": ["Worksheet is blocked until the hand-written policy and persona are complete."]}
    facts = desk_app.read_json(run_dir / "facts.json")
    report = report_path.read_text(encoding="utf-8", errors="replace")
    checks: list[str] = []
    expected_inputs = {
        "net_income": float(facts["net_income"]["val"]),
        "depreciation": float(facts["depreciation"]["val"]),
        "capex": abs(float(facts["capex"]["val"])),
    }
    for key, expected in expected_inputs.items():
        actual = float(calculations["owner_cash_flow"][key])
        if actual != expected:
            checks.append(f"Worksheet {key} input does not match facts.json.")
        fact = facts[key]
        if fact.get("tag") not in report or fact.get("end") not in report:
            checks.append(f"Worksheet does not cite the {key} tag and period end.")
        if f"{int(abs(expected)):,}" not in report:
            checks.append(f"Worksheet does not print the exact {key} input from facts.json.")
    expected_owner = expected_inputs["net_income"] + expected_inputs["depreciation"] - expected_inputs["capex"]
    if not math.isclose(float(calculations["owner_cash_flow"]["owner_cash_flow"]), expected_owner, rel_tol=0, abs_tol=1e-6):
        checks.append("Owner cash flow does not equal net income + depreciation - capex.")
    policy = desk_app.read_json(worksheet.DEFAULT_POLICY)
    if calculations.get("valuation_basis") != policy.get("valuation_basis"):
        checks.append("Worksheet valuation basis does not match config/worksheet_policy.json.")
    if calculations.get("deciding_number") != policy.get("deciding_number") or "Deciding number:" not in report:
        checks.append("Worksheet does not identify the policy's deciding number.")
    if "owner cash flow" not in report.lower() or "divide by diluted shares" not in report.lower():
        checks.append("Worksheet does not explain its owner-cash-flow per-share basis.")
    for case in ("bear", "base", "bull"):
        values = calculations["cases"][case]
        policy_case = policy.get("cases", {}).get(case, {})
        for rate in ("growth_rate", "discount_rate", "terminal_growth_rate"):
            if rate not in policy_case or not math.isclose(float(values[rate]), float(policy_case[rate]), rel_tol=0, abs_tol=1e-12):
                checks.append(f"{case.title()} {rate} does not match config/worksheet_policy.json.")
        try:
            recomputed = worksheet.calculate_dcf(
                expected_owner,
                float(values["growth_rate"]),
                float(values["discount_rate"]),
                float(values["terminal_growth_rate"]),
                int(calculations["years"]),
            )
            expected_value = recomputed["total_value"]
            expected_per_share = expected_value / float(facts["diluted_shares"]["val"])
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
            checks.append(f"Could not recompute {case} value case: {exc}")
            continue
        if not math.isclose(float(values["total_value"]), expected_value, rel_tol=1e-9, abs_tol=0.01):
            checks.append(f"{case.title()} total value does not match the printed formula.")
        if not math.isclose(float(values["per_share"]), expected_per_share, rel_tol=1e-9, abs_tol=0.01):
            checks.append(f"{case.title()} per-share value does not match the share count.")
        if f"${expected_per_share:,.2f}" not in report:
            checks.append(f"{case.title()} per-share value is not printed accurately in the worksheet.")
    shares = facts.get("diluted_shares", {})
    if shares.get("tag") not in report or shares.get("end") not in report:
        checks.append("Worksheet does not cite diluted shares and their period end.")
    if f"{int(float(shares.get('val', 0))):,}" not in report:
        checks.append("Worksheet does not print the exact diluted share count from facts.json.")
    market = json.loads((run_dir / "market_data.json").read_text(encoding="utf-8")) if (run_dir / "market_data.json").exists() else {}
    if market.get("close") is not None and f"${float(market['close']):,.2f}" not in report:
        checks.append("Worksheet market close does not match market_data.json.")
    if market.get("close_date") and str(market["close_date"]) not in report:
        checks.append("Worksheet market close date does not match market_data.json.")
    if calculations.get("margin_of_safety") is not None:
        expected_mos = float(calculations["margin_of_safety"])
        if not math.isclose(expected_mos, (float(calculations["cases"]["base"]["per_share"]) - float(market["close"])) / float(calculations["cases"]["base"]["per_share"]), rel_tol=1e-9, abs_tol=1e-9):
            checks.append("Margin of safety does not match base value and market close.")
        if f"{expected_mos:.2%}" not in report:
            checks.append("Margin of safety is not printed accurately in the worksheet.")
    equity = facts.get("equity", {})
    avg_equity = ((float(equity["val"]) + float(equity["prior_val"])) / 2
                  if equity.get("val") is not None and equity.get("prior_val") is not None else None)
    expected_roe = expected_inputs["net_income"] / avg_equity if avg_equity else None
    debt = float(facts["current_debt"]["val"]) + float(facts["long_term_debt"]["val"])
    equity_value = float(equity["val"]) if equity.get("val") else None
    expected_de = debt / equity_value if equity_value else None
    expected_decision = worksheet.evaluate_quantitative_rules(
        policy, expected_owner, calculations.get("margin_of_safety"), expected_roe,
        expected_de, float(market["close"]) if market.get("close") is not None else None,
        float(calculations["cases"]["base"]["per_share"]),
    )
    actual_decision = calculations.get("quantitative_decision", {})
    if actual_decision.get("rating") != expected_decision.get("rating"):
        checks.append("Quantitative rating does not match the written policy gates.")
    if not math.isclose(float(actual_decision.get("allocation_pct", -1)), float(expected_decision["allocation_pct"]), rel_tol=0, abs_tol=1e-9):
        checks.append("Allocation percentage does not match the written policy gates.")
    if expected_decision["rating"] not in report or f"{expected_decision['allocation_pct']:.1f}%" not in report:
        checks.append("Worksheet does not print the policy rating and allocation percentage.")
    portfolio_value = policy.get("client_portfolio_value_usd")
    expected_purchase = (float(portfolio_value) * float(expected_decision["allocation_pct"]) / 100
                         if portfolio_value is not None else None)
    actual_purchase = calculations.get("client_purchase_size_usd")
    if expected_purchase is None:
        if actual_purchase is not None or "not calculated because the team has not written a client portfolio value" not in report:
            checks.append("Worksheet must leave purchase dollars uncalculated when no client portfolio value is written.")
    elif actual_purchase is None or not math.isclose(float(actual_purchase), expected_purchase, rel_tol=0, abs_tol=0.01):
        checks.append("Dollar purchase size does not match client portfolio value and allocation.")
    return {"mark": "refused" if checks else "passed", "checks": checks or ["Worksheet inputs, sources, and arithmetic match saved facts."]}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check report numbers against saved filing text and XBRL facts.")
    parser.add_argument("run_dir", type=Path, help="Saved run folder with filing texts and facts.json")
    parser.add_argument("--report", type=Path, help="Report to check; defaults to verified_report.md")
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    report_path = (args.report or (run_dir / "verified_report.md")).resolve()
    if not run_dir.is_dir():
        parser.error(f"Run folder does not exist: {run_dir}")
    if not report_path.is_file():
        parser.error(f"Report does not exist: {report_path}")
    result = check_report(report_path, run_dir)
    worksheet_result = check_worksheet(run_dir) if (run_dir / "worksheet_output.md").exists() else None
    if worksheet_result:
        result["worksheet"] = worksheet_result
        if worksheet_result["mark"] == "refused":
            result["refused"] += 1
    verifier_result = check_verifier_marks(run_dir)
    result["verifier_marks"] = verifier_result
    if verifier_result["mark"] == "refused":
        result["refused"] += 1
    marks_path = run_dir / "evidence_hook_marks.json"
    marks_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Evidence hook: {result['passed']} passed; {result['refused']} refused")
    print(f"Saved marks: {marks_path}")
    for row in result["marks"]:
        if row["mark"] == "refused":
            first_line = row["claim"].splitlines()[0]
            reason = "; ".join(row["checks"])
            print(f"refused: {row['id']}: {first_line} — {reason}")
    return 1 if result["refused"] else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Evidence hook stopped: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
