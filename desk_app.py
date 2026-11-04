"""Run the EDGAR desk, then produce a four-role report through Purdue GenAI Studio."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from openai import APIError, APITimeoutError, OpenAI

import desk_steps


BASE = Path(__file__).resolve().parent
GENAI_BASE_URL = "https://genai.rcac.purdue.edu/api"
REQUIRED_PARTS = (
    "Overview",
    "Market Positioning and Growth Outlook",
    "Valuation Insights",
    "Future Developments and Strategic Recommendations",
    "Investment Recommendation",
)

ROLE_INSTRUCTIONS = {
    "Research Analyst": (
        "You are the Research Analyst. Use only the source text in the JSON context. "
        "Use only Item 1 Business, Item 7 MD&A, and the earnings release. Describe the "
        "business model, competitive position, catalysts, and recent developments. "
        "Support every factual claim with an exact quote from a numbered source line. "
        "For every quote, name the filename, line number, and filing accession. Do not "
        "add facts from memory, the web, or other sources. Do not calculate numbers. "
        "Return concise Markdown that can support the Overview, Market Positioning and "
        "Growth Outlook, and Future Developments and Strategic Recommendations parts. "
        "If the supplied sources do not support a claim, omit the claim."
    ),
    "Financial Analyst": (
        "You are the Financial Analyst. Use only the JSON context sent by the Strategy "
        "Manager. Use the supplied Step 4 facts, Step 5 code calculations, Step 6 release "
        "lines, and Step 7 peer facts. Do not calculate or estimate any number in the "
        "model. Copy the arithmetic and results from the code-calculator output. For each "
        "number, name its filing and its statement line or XBRL tag, period, and unit. "
        "For each ratio, give the formula and the arithmetic supplied by the calculator. "
        "State the definition used wherever the filing offers two definitions. Use these "
        "definitions: revenue growth is latest fiscal-year revenue divided by prior-year "
        "revenue, minus one; operating margin is operating income divided by total revenue; "
        "return on average equity is net income divided by average beginning and ending "
        "stockholders' equity; debt to equity is long-term debt, including its current "
        "portion, divided by stockholders' equity; free cash flow is cash from operations "
        "minus additions to property and equipment; P/E is share price divided by GAAP "
        "diluted EPS. Use the same operating-margin definition for each peer. Do not "
        "introduce numbers that are not in the supplied facts or calculations. Return "
        "concise Markdown for Valuation Insights and the report's financial analysis."
    ),
    "Investment Advisor": (
        "You are the Investment Advisor. Use only the Research Analyst and Financial "
        "Analyst outputs in the JSON context. Do not use other information. Give a short "
        "thesis and one recommendation: Buy, Hold, or Sell. Name one number that decides "
        "the recommendation. Use only a number stated by the Financial Analyst. Explain "
        "why that number supports the recommendation. Do not invent facts or calculate. "
        "Return concise Markdown for Investment Recommendation and any strategic action."
    ),
}

MANAGER_INSTRUCTIONS = (
    "You are the Strategy Manager for a four-role equity research desk. You receive the "
    "Research Analyst, Financial Analyst, and Investment Advisor outputs. Check that the "
    "five report parts are present and consistent. The five parts are: Overview; Market "
    "Positioning and Growth Outlook; Valuation Insights; Future Developments and Strategic "
    "Recommendations; Investment Recommendation. Check that the Advisor uses only the "
    "Research Analyst and Financial Analyst outputs, and that every report number comes "
    "from the Financial Analyst output. Do not add facts or numbers. Do not repair a source "
    "claim yourself. If a part is missing or inconsistent, name the part, the responsible "
    "role, and the exact problem. The code will send each failing part back to its role once. "
    "Return one valid JSON object and no other text. Use this schema: "
    '{"checks":[{"part":"Overview","status":"pass or fail",'
    '"responsible_role":"Research Analyst, Financial Analyst, or Investment Advisor",'
    '"problem":"empty when pass"}],"report_markdown":"Markdown report with all five parts"}. '
    "Use these exact Markdown headings: ## Overview; ## Market Positioning and Growth Outlook; "
    "## Valuation Insights; ## Future Developments and Strategic Recommendations; "
    "## Investment Recommendation. The code adds the filing list and run time before the report."
)


def model_call(
    client: OpenAI,
    model: str,
    role: str,
    instructions: str,
    payload: dict[str, Any],
    max_tokens: int,
) -> str:
    print(f"ROLE: {role}", flush=True)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        max_tokens=max_tokens,
        temperature=0.2,
        stream=True,
    )
    chunks: list[str] = []
    for event in response:
        if event.choices and event.choices[0].delta.content:
            chunks.append(event.choices[0].delta.content)
    content = "".join(chunks).strip()
    if not content:
        raise RuntimeError(f"{role} returned an empty response")
    return content


def parse_json_object(text: str) -> dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    first = cleaned.find("{")
    last = cleaned.rfind("}")
    if first < 0 or last < first:
        raise ValueError("Strategy Manager did not return a JSON object")
    value = json.loads(cleaned[first : last + 1])
    if not isinstance(value, dict):
        raise ValueError("Strategy Manager JSON is not an object")
    return value


def latest_section(lines: list[str], start_pattern: str, end_pattern: str) -> str:
    start_re = re.compile(start_pattern, re.I)
    end_re = re.compile(end_pattern, re.I)
    starts = [i for i, line in enumerate(lines) if start_re.match(line.strip())]
    if not starts:
        raise ValueError(f"Could not find filing section: {start_pattern}")
    start = starts[-1]
    end = next((i for i in range(start + 1, len(lines)) if end_re.match(lines[i].strip())), None)
    if end is None:
        raise ValueError(f"Could not find the end of filing section: {start_pattern}")
    return "\n".join(f"{i + 1:05d}: {lines[i]}" for i in range(start, end) if lines[i].strip())


def numbered_lines(path: Path) -> str:
    return "\n".join(
        f"{i:05d}: {line}" for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if line.strip()
    )


def extract_output_lines(stdout: str, starts: tuple[str, ...], stops: tuple[str, ...]) -> str:
    lines = stdout.splitlines()
    selected: list[str] = []
    active = False
    for line in lines:
        if any(marker in line for marker in starts):
            active = True
        if active and any(marker in line for marker in stops):
            break
        if active:
            selected.append(line)
    return "\n".join(selected)


def run_data_steps(args: argparse.Namespace) -> tuple[Path, str]:
    command = [sys.executable, str(BASE / "desk_steps.py"), args.ticker.upper()]
    if args.peers:
        command.extend(["--peers", args.peers])
    if args.price is not None:
        command.extend(["--price", str(args.price)])
    completed = subprocess.run(
        command,
        cwd=BASE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    if completed.stdout:
        print(completed.stdout, end="", flush=True)
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="", flush=True)
    if completed.returncode:
        raise RuntimeError(f"Seven-step desk exited with code {completed.returncode}")
    match = re.search(r"Saved primary-company filings and facts to:\s*(.+)", completed.stdout)
    if not match:
        raise RuntimeError("Could not find the primary run folder in the seven-step output")
    return Path(match.group(1).strip()), completed.stdout


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def filing_header(ticker: str, filings: dict[str, Any], peers: list[str], run_dir: Path) -> str:
    rows = [
        f"{ticker.upper()} 10-K accession {filings['10-K']['accession']}",
        f"{ticker.upper()} 10-Q accession {filings['10-Q']['accession']}",
        f"{ticker.upper()} 8-K Exhibit 99.1 accession {filings['earnings_8k']['accession']}",
    ]
    for peer in peers:
        fact = read_json(run_dir / f"{peer}_facts.json")
        accession = fact["total_revenue"]["accn"]
        rows.append(f"{peer} latest 10-K accession {accession}")
    return "Filings read: " + "; ".join(rows)


def build_financial_context(
    ticker: str,
    peers: list[str],
    run_dir: Path,
    stdout: str,
    args: argparse.Namespace,
) -> dict[str, Any]:
    primary_facts = read_json(run_dir / "facts.json")
    peer_facts = {p: read_json(run_dir / f"{p}_facts.json") for p in peers}
    filings = read_json(run_dir / "filings.json")
    tenk_path = run_dir / f"10-K_{filings['10-K']['date']}.txt"
    tenk_lines = tenk_path.read_text(encoding="utf-8").splitlines()
    statement_names = (
        "Total revenue", "Operating income", "NET INCOME", "Diluted |",
        "TOTAL EQUITY", "Current portion of long-term debt", "Long-term debt, excluding current portion",
        "Net cash provided by operating activities", "Additions to property and equipment",
    )
    statement_evidence = [
        {"line": i, "text": line}
        for i, line in enumerate(tenk_lines, 1)
        if any(name.lower() in line.lower() for name in statement_names)
    ]
    release_path = run_dir / f"8-K_Ex99.1_{filings['earnings_8k']['date']}.txt"
    release_lines = numbered_lines(release_path)
    peer_logs = extract_output_lines(stdout, ("STEP 7",), ("Saved primary-company",))
    ratio_logs = extract_output_lines(stdout, ("STEP 5",), ("STEP 6",))
    quarterly_logs = extract_output_lines(stdout, ("STEP 6",), ("STEP 7",))
    return {
        "ticker": ticker.upper(),
        "filings": filings,
        "primary_company_facts": primary_facts,
        "primary_10k_statement_lines": {
            "filename": tenk_path.name,
            "accession": filings["10-K"]["accession"],
            "lines": statement_evidence,
        },
        "calculator_output_from_step_5": ratio_logs,
        "quarterly_release_output_from_step_6": quarterly_logs,
        "quarterly_release_line_numbered_source": {
            "filename": release_path.name,
            "accession": filings["earnings_8k"]["accession"],
            "lines": release_lines,
        },
        "peer_facts_from_step_7": peer_facts,
        "peer_calculator_output_from_step_7": peer_logs,
        "price_input": {
            "value": args.price,
            "date": args.price_date,
            "source": args.price_source,
        },
        "instruction": "Use only these facts. Do not calculate. The values in calculator output were calculated by code.",
    }


def build_research_context(run_dir: Path, filings: dict[str, Any]) -> dict[str, Any]:
    tenk_path = run_dir / f"10-K_{filings['10-K']['date']}.txt"
    lines = tenk_path.read_text(encoding="utf-8").splitlines()
    business = latest_section(
        lines,
        r"ITEM\s*1\W*B\s*U\s*S\s*I\s*N\s*E\s*S\s*S\s*$",
        r"ITEM\s*1A\b",
    )
    mda = latest_section(
        lines,
        r"ITEM\s*7(?!A)\b.*DISCUSSION AND ANALYSIS.*$",
        r"ITEM\s*8\b.*$",
    )
    release_path = run_dir / f"8-K_Ex99.1_{filings['earnings_8k']['date']}.txt"
    return {
        "filings": {
            "10-K": {
                "filename": tenk_path.name,
                "accession": filings["10-K"]["accession"],
            },
            "earnings_release": {
                "filename": release_path.name,
                "accession": filings["earnings_8k"]["accession"],
                "exhibit": filings["earnings_8k"].get("exhibit_99_1"),
            },
        },
        "item_1_business_line_numbered_text": business,
        "item_7_mda_line_numbered_text": mda,
        "earnings_release_line_numbered_text": numbered_lines(release_path),
        "instruction": "Quote source lines exactly. Cite the filename, line, and accession for every claim.",
    }


def role_payload(task: str, context: Any, expected_output: str) -> dict[str, Any]:
    return {"task": task, "context": context, "expected_output": expected_output}


def manager_payload(role_outputs: dict[str, str], retry: bool = False) -> dict[str, Any]:
    return role_payload(
        "Check the role outputs against the five required report parts. Identify missing or inconsistent parts and compile the report.",
        {"role_outputs": role_outputs, "revision_already_used": retry},
        "One JSON object with checks and report_markdown, using the required schema.",
    )


def status_checks(manager: dict[str, Any], report: str) -> list[dict[str, str]]:
    raw_checks = manager.get("checks", [])
    checks: dict[str, dict[str, str]] = {}
    if isinstance(raw_checks, list):
        for item in raw_checks:
            if isinstance(item, dict) and item.get("part") in REQUIRED_PARTS:
                checks[item["part"]] = {
                    "part": item["part"],
                    "status": str(item.get("status", "fail")).lower(),
                    "responsible_role": str(item.get("responsible_role", "Research Analyst")),
                    "problem": str(item.get("problem", "")),
                }
    for part in REQUIRED_PARTS:
        heading_ok = re.search(rf"^##\s+{re.escape(part)}\s*$", report, re.M) is not None
        item = checks.setdefault(
            part,
            {"part": part, "status": "pass", "responsible_role": "Research Analyst", "problem": ""},
        )
        if not heading_ok:
            item["status"] = "fail"
            item["problem"] = (item["problem"] + " Required Markdown heading is missing.").strip()
    return list(checks.values())


def responsible_role(part: str, check: dict[str, str]) -> str:
    role = check["responsible_role"]
    if role in ROLE_INSTRUCTIONS:
        return role
    if part == "Investment Recommendation":
        return "Investment Advisor"
    if part == "Valuation Insights":
        return "Financial Analyst"
    return "Research Analyst"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(description="Run the seven-step desk and its four model roles.")
    parser.add_argument("ticker")
    parser.add_argument("--peers", default="", help="Comma-separated peer tickers")
    parser.add_argument("--price", type=float, help="Share price used for P/E")
    parser.add_argument("--price-date", help="Date for the supplied closing price, YYYY-MM-DD")
    parser.add_argument("--price-source", help="Source of the supplied closing price")
    args = parser.parse_args()
    if args.price is not None and not args.price_date:
        parser.error("--price-date is required when --price is used")
    if args.price is not None and not args.price_source:
        parser.error("--price-source is required when --price is used")

    env = desk_steps.read_env(BASE / ".env")
    api_key = env.get("API_KEY", "").strip()
    model = env.get("MODEL", "").strip()
    if not api_key:
        raise RuntimeError(".env must contain API_KEY")
    if not model:
        raise RuntimeError(".env must contain MODEL")

    peers = [p.strip().upper() for p in args.peers.split(",") if p.strip()]
    run_dir, stdout = run_data_steps(args)
    filings = read_json(run_dir / "filings.json")
    report_time = datetime.now().astimezone().isoformat(timespec="seconds")
    manager_header = filing_header(args.ticker, filings, peers, run_dir)

    client = OpenAI(api_key=api_key, base_url=GENAI_BASE_URL, timeout=900, max_retries=0)
    research_payload = role_payload(
        "Write evidence-based research for the report. Address the business model, competitive position, catalysts, and recent developments.",
        build_research_context(run_dir, filings),
        "Concise Markdown. Quote every factual claim and cite filename, source line, and accession.",
    )
    financial_payload = role_payload(
        "Write the financial analysis for the report from the supplied step outputs.",
        build_financial_context(args.ticker, peers, run_dir, stdout, args),
        "Concise Markdown. Include each source, period, unit, definition, and supplied arithmetic.",
    )
    role_payloads: dict[str, dict[str, Any]] = {
        "Research Analyst": research_payload,
        "Financial Analyst": financial_payload,
    }
    outputs: dict[str, str] = {}
    outputs["Research Analyst"] = model_call(
        client, model, "Research Analyst", ROLE_INSTRUCTIONS["Research Analyst"], research_payload, 1800
    )
    outputs["Financial Analyst"] = model_call(
        client, model, "Financial Analyst", ROLE_INSTRUCTIONS["Financial Analyst"], financial_payload, 1600
    )

    advisor_payload = role_payload(
        "Write the thesis and investment recommendation.",
        {"Research Analyst": outputs["Research Analyst"], "Financial Analyst": outputs["Financial Analyst"]},
        "Concise Markdown. Give one of Buy, Hold, or Sell. Name one deciding number from the Financial Analyst output.",
    )
    role_payloads["Investment Advisor"] = advisor_payload
    outputs["Investment Advisor"] = model_call(
        client, model, "Investment Advisor", ROLE_INSTRUCTIONS["Investment Advisor"], advisor_payload, 800
    )

    manager_response = model_call(
        client, model, "Strategy Manager", MANAGER_INSTRUCTIONS, manager_payload(outputs), 3000
    )
    manager_data = parse_json_object(manager_response)
    report_body = str(manager_data.get("report_markdown", "")).strip()
    if not report_body:
        raise RuntimeError("Strategy Manager JSON did not include report_markdown")
    checks = status_checks(manager_data, report_body)

    failed_by_role: dict[str, list[dict[str, str]]] = {}
    for check in checks:
        if check["status"] not in ("pass", "passed", "ok"):
            role = responsible_role(check["part"], check)
            failed_by_role.setdefault(role, []).append(check)

    for role, failures in failed_by_role.items():
        original = role_payloads[role]
        revision_context = {
            "original_context": original["context"],
            "revision_requests": [
                {"part": item["part"], "problem": item["problem"]} for item in failures
            ],
        }
        retry_payload = role_payload(
            f"Revise only the named failing report part or parts. This is the one permitted revision for each part.",
            revision_context,
            original["expected_output"],
        )
        outputs[role] = model_call(
            client,
            model,
            role,
            ROLE_INSTRUCTIONS[role],
            retry_payload,
            1800 if role == "Research Analyst" else 1600 if role == "Financial Analyst" else 800,
        )

    if failed_by_role:
        # The manager compiles once more after the permitted role revisions. No role gets a second revision.
        manager_response = model_call(
            client,
            model,
            "Strategy Manager",
            MANAGER_INSTRUCTIONS + " This is the final compile. Do not request further revisions.",
            manager_payload(outputs, retry=True),
            3000,
        )
        manager_data = parse_json_object(manager_response)
        report_body = str(manager_data.get("report_markdown", "")).strip()
        checks = status_checks(manager_data, report_body)

    unresolved = [c for c in checks if c["status"] not in ("pass", "passed", "ok")]
    if unresolved:
        warning = "\n\n> Manager check: the following part(s) still need review after the one permitted revision: "
        warning += "; ".join(f"{c['part']}: {c['problem']}" for c in unresolved)
        report_body += warning

    report = f"{manager_header}\nRun time: {report_time}\n\n{report_body}\n"
    report_path = run_dir / f"{args.ticker.upper()}_equity_research_report.md"
    report_path.write_text(report, encoding="utf-8")
    (run_dir / "role_outputs.json").write_text(json.dumps(outputs, indent=2, ensure_ascii=False), encoding="utf-8")
    (run_dir / "manager_checks.json").write_text(json.dumps(checks, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved report: {report_path}")
    if unresolved:
        print("Manager check needs review for: " + ", ".join(c["part"] for c in unresolved))


if __name__ == "__main__":
    try:
        main()
    except APITimeoutError:
        print(
            "Purdue GenAI Studio did not return a model response before the request timed out. "
            "The seven-step data run is saved. Run this command again when the model service responds.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    except APIError as exc:
        status = getattr(exc, "status_code", None)
        status_text = f"HTTP {status}" if status else "API error"
        print(
            f"Purdue GenAI Studio returned {status_text}. The seven-step data run is saved. "
            "No model report was written.",
            file=sys.stderr,
        )
        raise SystemExit(1)
