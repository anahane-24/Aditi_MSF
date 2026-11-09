"""Fixed CrewAI Flow team for the seven-step SEC equity desk."""

from __future__ import annotations

import argparse
import ast
import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from crewai import LLM
from crewai.flow import Flow, listen, start
from pydantic import BaseModel, Field

import desk_app
import desk_steps


BASE = Path(__file__).resolve().parent
ROLE_DIR = BASE / "roles"
ROLE_FILES = {
    "Research Analyst": "research_analyst.md",
    "Financial Analyst": "financial_analyst.md",
    "Investment Advisor": "investment_advisor.md",
    "Strategy Manager": "strategy_manager.md",
    "Verifier": "verifier.md",
}
ANALYST_ROLES = ("Research Analyst", "Financial Analyst", "Investment Advisor")
REQUIRED_PARTS = desk_app.REQUIRED_PARTS
GLOBAL_MODEL: LLM | None = None


TeamState = dict[str, Any]


class DeskTeamState(BaseModel):
    ticker: str = ""
    peers: list[str] = Field(default_factory=list)
    price: float | None = None
    price_date: str | None = None
    price_source: str | None = None
    run_dir: str = ""
    run_time: str = ""
    step_stdout: str = ""
    filings: dict[str, Any] = Field(default_factory=dict)
    facts: dict[str, Any] = Field(default_factory=dict)
    peer_facts: dict[str, Any] = Field(default_factory=dict)
    role_payloads: dict[str, dict[str, Any]] = Field(default_factory=dict)
    role_outputs: dict[str, str] = Field(default_factory=dict)
    manager_checks: list[dict[str, str]] = Field(default_factory=list)
    retry_queue: list[dict[str, Any]] = Field(default_factory=list)
    current_retry: dict[str, Any] = Field(default_factory=dict)
    retry_used: dict[str, bool] = Field(default_factory=dict)
    next_route: str = ""
    report_body: str = ""
    report_path: str = ""
    verification_items: list[dict[str, Any]] = Field(default_factory=list)
    verification_rows: list[dict[str, str]] = Field(default_factory=list)
    verifier_status: str = ""
    node_counts: dict[str, int] = Field(default_factory=dict)


def load_role(role: str) -> str:
    path = ROLE_DIR / ROLE_FILES[role]
    return path.read_text(encoding="utf-8")


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def save_node_event(
    run_dir: Path,
    name: str,
    attempt: int,
    node_input: Any,
    node_output: Any,
) -> None:
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_").lower()
    folder = run_dir / "node_io"
    save_json(folder / f"{safe}_attempt_{attempt}_input.json", node_input)
    save_json(folder / f"{safe}_attempt_{attempt}_output.json", node_output)


def start_node(state: TeamState, name: str) -> tuple[int, dict[str, int]]:
    print(f"NODE: {name}", flush=True)
    counts = dict(state.get("node_counts", {}))
    role = next((item for item in ROLE_FILES if name == item or name.startswith(item + " (")), None)
    if role:
        role_calls = sum(value for node, value in counts.items() if node == role or node.startswith(role + " ("))
        if role_calls >= 2:
            raise RuntimeError(f"The {role} role cannot run more than twice in one run")
    attempt = counts.get(name, 0) + 1
    counts[name] = attempt
    return attempt, counts


def message_text(message: Any) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        pieces: list[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                pieces.append(item["text"])
            elif isinstance(item, str):
                pieces.append(item)
        return "\n".join(pieces).strip()
    return str(content).strip()


def call_model(role: str, payload: dict[str, Any], *, final_compile: bool = False) -> str:
    if GLOBAL_MODEL is None:
        raise RuntimeError("Model client is not configured")
    instruction = load_role(role)
    if role == "Strategy Manager" and final_compile:
        instruction += "\n\nThis is the final compile. Do not request more revisions."
    print(f"ROLE: {role}", flush=True)
    response = GLOBAL_MODEL.call(
        messages=[
            {"role": "system", "content": instruction},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ]
    )
    text = message_text(response)
    if not text:
        raise RuntimeError(f"{role} returned an empty response")
    return text


def as_json(text: str, who: str) -> dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    decoder = json.JSONDecoder()
    decoded: list[Any] = []
    cursor = 0
    while cursor < len(cleaned):
        starts = [index for index in (cleaned.find("{", cursor), cleaned.find("[", cursor)) if index >= 0]
        if not starts:
            break
        left = min(starts)
        value, end = decoder.raw_decode(cleaned[left:])
        decoded.append(value)
        cursor = left + end
    if not decoded:
        raise ValueError(f"{who} did not return a JSON object")
    if len(decoded) == 1 and isinstance(decoded[0], dict) and "items" in decoded[0]:
        result = decoded[0]
    else:
        entries: list[Any] = []
        for value in decoded:
            if isinstance(value, dict) and isinstance(value.get("items"), list):
                entries.extend(value["items"])
            elif isinstance(value, dict) and ("item_id" in value or ("id" in value and "mark" in value)):
                entries.append({"id": value.get("id", value.get("item_id")), **value})
            elif isinstance(value, list):
                entries.extend(value)
        result = {"items": entries} if entries else decoded[0]
    if not isinstance(result, dict):
        raise ValueError(f"{who} JSON result is not an object")
    return result


def create_data_steps(state: TeamState) -> dict[str, Any]:
    attempt, counts = start_node(state, "Steps")
    args = argparse.Namespace(
        ticker=state["ticker"],
        peers=",".join(state.get("peers", [])),
        price=state.get("price"),
        price_date=state.get("price_date"),
        price_source=state.get("price_source"),
    )
    run_dir, stdout = desk_app.run_data_steps(args)
    run_time = datetime.now().astimezone().isoformat(timespec="seconds")
    filings = desk_app.read_json(run_dir / "filings.json")
    facts = desk_app.read_json(run_dir / "facts.json")
    peers = {
        symbol: desk_app.read_json(run_dir / f"{symbol}_facts.json")
        for symbol in state.get("peers", [])
        if (run_dir / f"{symbol}_facts.json").exists()
    }
    node_input = {
        "ticker": state["ticker"],
        "peers": state.get("peers", []),
        "price": state.get("price"),
        "price_date": state.get("price_date"),
        "price_source": state.get("price_source"),
    }
    node_output = {
        "data_run_folder": str(run_dir),
        "saved_files": sorted(p.name for p in run_dir.iterdir() if p.is_file()),
        "steps_completed": [f"STEP {i}" for i in range(1, 8)],
    }
    save_node_event(run_dir, "Steps", attempt, node_input, node_output)
    save_json(
        run_dir / "run_metadata.json",
        {
            **node_input,
            "run_time": run_time,
            "step_output_file": "step_output.txt",
            "framework": "CrewAI Flow",
        },
    )
    (run_dir / "step_output.txt").write_text(stdout, encoding="utf-8")
    return {
        "run_dir": str(run_dir),
        "run_time": run_time,
        "step_stdout": stdout,
        "filings": filings,
        "facts": facts,
        "peer_facts": peers,
        "node_counts": counts,
    }


def make_role_payloads(state: TeamState) -> dict[str, dict[str, Any]]:
    run_dir = Path(state["run_dir"])
    filings = state["filings"]
    research_context = desk_app.build_research_context(run_dir, filings)
    financial_context = desk_app.build_financial_context(
        state["ticker"],
        state.get("peers", []),
        run_dir,
        state["step_stdout"],
        argparse.Namespace(
            price=state.get("price"),
            price_date=state.get("price_date"),
            price_source=state.get("price_source"),
        ),
    )
    research = desk_app.role_payload(
        "Write evidence-based research for the five-part report. Address the business model, competitive position, catalysts, and recent developments.",
        research_context,
        "Concise Markdown. Quote every factual claim. Cite the exact filename, line, and accession.",
    )
    financial = desk_app.role_payload(
        "Write the financial analysis from the supplied seven-step desk output.",
        financial_context,
        "Concise Markdown. Include each source, period, unit, definition, and supplied arithmetic.",
    )
    return {"Research Analyst": research, "Financial Analyst": financial}


def role_node(role: str):
    def run(state: TeamState) -> dict[str, Any]:
        attempt, counts = start_node(state, role)
        payloads = state.get("role_payloads") or make_role_payloads(state)
        payload = payloads[role]
        run_dir = Path(state["run_dir"])
        save_node_event(run_dir, role, attempt, payload, {"status": "started"})
        try:
            output = call_model(role, payload)
        except Exception as exc:
            save_node_event(run_dir, role, attempt, payload, {"error": repr(exc)})
            raise
        save_node_event(run_dir, role, attempt, payload, {"output": output})
        outputs = dict(state.get("role_outputs", {}))
        outputs[role] = output
        save_json(run_dir / "role_outputs.json", outputs)
        return {"role_payloads": payloads, "role_outputs": outputs, "node_counts": counts}

    return run


def run_investment_advisor_node(state: TeamState) -> dict[str, Any]:
    role = "Investment Advisor"
    attempt, counts = start_node(state, role)
    outputs = state["role_outputs"]
    payload = desk_app.role_payload(
        "Write the thesis and one investment recommendation.",
        {
            "Research Analyst": outputs["Research Analyst"],
            "Financial Analyst": outputs["Financial Analyst"],
        },
        "Concise Markdown. Give one of Buy, Hold, or Sell. Name one deciding number from the Financial Analyst output.",
    )
    payloads = dict(state.get("role_payloads", {}))
    payloads[role] = payload
    run_dir = Path(state["run_dir"])
    save_node_event(run_dir, role, attempt, payload, {"status": "started"})
    try:
        output = call_model(role, payload)
    except Exception as exc:
        save_node_event(run_dir, role, attempt, payload, {"error": repr(exc)})
        raise
    save_node_event(run_dir, role, attempt, payload, {"output": output})
    outputs = dict(outputs)
    outputs[role] = output
    save_json(run_dir / "role_outputs.json", outputs)
    return {"role_payloads": payloads, "role_outputs": outputs, "node_counts": counts}


def manager_payload(state: TeamState, *, final: bool = False) -> dict[str, Any]:
    task = (
        "Compile the final report from the revised role outputs. Do not request another revision."
        if final
        else "Check the role outputs against the five required parts, identify any failing part and its responsible role, and compile the report."
    )
    context = {
        "role_outputs": state["role_outputs"],
        "previous_checks": state.get("manager_checks", []),
        "revisions_used": state.get("retry_used", {}),
    }
    return desk_app.role_payload(
        task,
        context,
        "One JSON object with checks and report_markdown, using the Strategy Manager schema.",
    )


def retry_queue_from_checks(checks: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for check in checks:
        if check["status"] in ("pass", "passed", "ok"):
            continue
        role = desk_app.responsible_role(check["part"], check)
        if role not in ANALYST_ROLES:
            role = "Research Analyst"
        grouped.setdefault(role, []).append(
            {"part": check["part"], "problem": check["problem"] or "The part failed the Manager check."}
        )
    return [{"role": role, "requests": requests} for role, requests in grouped.items()]


def strategy_manager_node(state: TeamState) -> dict[str, Any]:
    role = "Strategy Manager"
    attempt, counts = start_node(state, role)
    payload = manager_payload(state)
    run_dir = Path(state["run_dir"])
    save_node_event(run_dir, role, attempt, payload, {"status": "started"})
    try:
        raw = call_model(role, payload)
        parsed = as_json(raw, role)
        report = str(parsed.get("report_markdown", "")).strip()
        if not report:
            raise ValueError("Strategy Manager did not return report_markdown")
        checks = desk_app.status_checks(parsed, report)
        queue = retry_queue_from_checks(checks)
        used = dict(state.get("retry_used", {}))
        queue = [item for item in queue if not used.get(item["role"], False)]
        result = {
            "checks": checks,
            "retry_queue": queue,
            "report_markdown": report,
        }
    except Exception as exc:
        save_node_event(run_dir, role, attempt, payload, {"error": repr(exc)})
        raise
    save_node_event(run_dir, role, attempt, payload, result)
    save_json(run_dir / "manager_checks.json", checks)
    return {
        "manager_checks": checks,
        "retry_queue": queue,
        "report_body": report,
        "node_counts": counts,
    }


def manager_route(state: TeamState) -> str:
    return "retry_dispatch" if state.get("retry_queue") else "verifier"


def retry_dispatch_node(state: TeamState) -> dict[str, Any]:
    attempt, counts = start_node(state, "Retry Router")
    queue = list(state.get("retry_queue", []))
    run_dir = Path(state["run_dir"])
    if not queue:
        output = {"next_route": "manager_compile", "retry_queue": []}
        save_node_event(run_dir, "Retry Router", attempt, {"queue": []}, output)
        return {**output, "node_counts": counts}
    current = queue.pop(0)
    output = {"next_route": current["role"], "current_retry": current, "retry_queue": queue}
    save_node_event(run_dir, "Retry Router", attempt, {"queue": state.get("retry_queue", [])}, output)
    return {**output, "node_counts": counts}


def retry_route(state: TeamState) -> str:
    role = state.get("next_route", "manager_compile")
    return {
        "Research Analyst": "retry_research",
        "Financial Analyst": "retry_financial",
        "Investment Advisor": "retry_advisor",
        "manager_compile": "manager_compile",
    }.get(role, "manager_compile")


def retry_role_node(role: str):
    def run(state: TeamState) -> dict[str, Any]:
        node_name = f"{role} (retry 1)"
        attempt, counts = start_node(state, node_name)
        requested = state.get("current_retry", {})
        original = state["role_payloads"][role]
        payload = desk_app.role_payload(
            "Revise only the named failing part or parts. This is the one permitted revision for this role.",
            {
                "original_context": original["context"],
                "previous_output": state["role_outputs"].get(role, ""),
                "revision_requests": requested.get("requests", []),
            },
            original["expected_output"],
        )
        run_dir = Path(state["run_dir"])
        save_node_event(run_dir, node_name, attempt, payload, {"status": "started"})
        try:
            output = call_model(role, payload)
        except Exception as exc:
            save_node_event(run_dir, node_name, attempt, payload, {"error": repr(exc)})
            raise
        save_node_event(run_dir, node_name, attempt, payload, {"output": output})
        outputs = dict(state["role_outputs"])
        outputs[role] = output
        used = dict(state.get("retry_used", {}))
        used[role] = True
        save_json(run_dir / "role_outputs.json", outputs)
        return {"role_outputs": outputs, "retry_used": used, "node_counts": counts}

    return run


def final_compile_node(state: TeamState) -> dict[str, Any]:
    role = "Strategy Manager"
    attempt, counts = start_node(state, "Strategy Manager (final compile)")
    payload = manager_payload(state, final=True)
    run_dir = Path(state["run_dir"])
    save_node_event(run_dir, "Strategy Manager (final compile)", attempt, payload, {"status": "started"})
    try:
        raw = call_model(role, payload, final_compile=True)
        parsed = as_json(raw, role)
        report = str(parsed.get("report_markdown", "")).strip()
        if not report:
            raise ValueError("Final Strategy Manager call did not return report_markdown")
        checks = desk_app.status_checks(parsed, report)
        result = {"checks": checks, "report_markdown": report}
    except Exception as exc:
        save_node_event(run_dir, "Strategy Manager (final compile)", attempt, payload, {"error": repr(exc)})
        raise
    save_node_event(run_dir, "Strategy Manager (final compile)", attempt, payload, result)
    save_json(run_dir / "manager_checks.json", checks)
    return {"manager_checks": checks, "report_body": report, "node_counts": counts}


def arithmetic_result(block: str) -> tuple[bool | None, str]:
    if "=" not in block:
        return None, "No explicit arithmetic expression."
    parts = block.split("=")
    if len(parts) < 2:
        return None, "No explicit arithmetic expression."
    expression = parts[-2] if len(parts) > 2 else parts[0]
    result_text = parts[-1]
    expression = re.sub(r"(?i)\b(?:million|millions|billion|billions|usd|shares|per share)\b", "", expression)
    expression = expression.replace(",", "").replace("$", "").replace("%", "").replace("*", "").replace("`", "").strip().rstrip(".")
    target_match = re.search(r"[-+]?\d+(?:\.\d+)?", result_text.replace(",", ""))
    if not target_match:
        return None, "Could not read the printed arithmetic result."
    target = float(target_match.group(0))
    percentage = "%" in result_text
    try:
        parsed = ast.parse(expression, mode="eval")
        def evaluate(node: ast.AST) -> float:
            if isinstance(node, ast.Expression): return evaluate(node.body)
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)): return float(node.value)
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                value = evaluate(node.operand)
                return value if isinstance(node.op, ast.UAdd) else -value
            if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
                left, right = evaluate(node.left), evaluate(node.right)
                if isinstance(node.op, ast.Add): return left + right
                if isinstance(node.op, ast.Sub): return left - right
                if isinstance(node.op, ast.Mult): return left * right
                if right == 0: raise ZeroDivisionError
                return left / right
            raise ValueError("Unsupported arithmetic expression")
        value = evaluate(parsed)
        if percentage:
            value *= 100
        precision = len(target_match.group(0).partition(".")[2])
        displayed = round(value, precision)
        ok = displayed == target
        return ok, f"Code recalculated {displayed:.{precision}f}{'%' if percentage else ''}; report prints {target:g}{'%' if percentage else ''}."
    except Exception as exc:
        return None, f"Could not safely recalculate the expression: {exc}"


def ratio_definition_result(block: str) -> tuple[bool | None, str]:
    text = block.lower()
    requirements = (
        (r"revenue growth", ("revenue", "prior")),
        (r"operating margin", ("operating income", "revenue")),
        (r"return on average equity|return on equity|\broae\b|\broe\b", ("net income", "average", "equity")),
        (r"debt\s*(?:to|/)\s*equity", ("debt", "current", "equity")),
        (r"free cash flow|\bfcf\b", ("cash from operations", "property and equipment")),
        (r"\bp\s*/\s*e\b|price.?to.?earnings", ("price", "diluted eps")),
    )
    for pattern, terms in requirements:
        if re.search(pattern, text, re.I):
            missing = [term for term in terms if term not in text]
            if missing:
                return False, f"Ratio definition is missing: {', '.join(missing)}."
            if "=" not in block and not re.search(r"\bdivided by\b|\bminus\b", text):
                return False, "Ratio definition does not state its arithmetic."
            return True, "Ratio definition states its inputs and arithmetic."
    return None, "No named ratio definition in this claim."


def normalized_quote(text: str) -> str:
    text = html.unescape(text).replace("\xa0", " ").lower()
    return re.sub(r"[^a-z0-9]", "", text)


def report_blocks(report: str) -> list[dict[str, str]]:
    lines = report.splitlines()
    blocks: list[str] = []
    current: list[str] = []
    in_recommendation = False
    table_period_header = ""
    for line in lines:
        if line.strip().lower().startswith("## investment recommendation"):
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            in_recommendation = True
        if in_recommendation:
            continue
        if line.startswith("Filings read:") or line.startswith("Run time:"):
            continue
        if not line.strip():
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            table_period_header = ""
            continue
        if line.lstrip().startswith("## "):
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            table_period_header = ""
            continue
        if line.lstrip().startswith("|"):
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            table_row = line.strip()
            if re.search(r"\bFY\s*20\d{2}\b", table_row, re.I) and not re.search(r"\$\s*\d", table_row):
                table_period_header = table_row
                continue
            if re.match(r"^\|\s*:?-{2,}", table_row):
                continue
            blocks.append(f"{table_period_header}\n{table_row}" if table_period_header else table_row)
            continue
        if line.startswith("-") and current and not current[0].startswith("  "):
            blocks.append("\n".join(current).strip())
            current = [line]
        elif current and (line.startswith("  ") or line.startswith(">")):
            current.append(line)
        else:
            if current:
                blocks.append("\n".join(current).strip())
            current = [line]
    if current:
        blocks.append("\n".join(current).strip())

    result: list[dict[str, str]] = []
    for block in blocks:
        if re.match(r"^\|\s*:?-{2,}", block) or re.match(r"^\|\s*[^|]+\|\s*[-: ]+\|?$", block):
            continue
        claim_scan = re.sub(r"\b(?:line|lines|page|pages)\s+\d+(?:\s*[-–]\s*\d+)?", "", block, flags=re.I)
        claim_scan = re.sub(r"\b(?:accession|CIK)\s+\S+", "", claim_scan, flags=re.I)
        claim_scan = re.sub(r"\b(?:FY|fiscal year)\s*20\d{2}\b", "", claim_scan, flags=re.I)
        claim_scan = re.sub(r"\b20\d{2}-\d{2}-\d{2}\b", "", claim_scan)
        if re.search(r"(?:\$|%|\b\d[\d,]*(?:\.\d+)?\s*(?:billion|million|basis points|bps)\b)", claim_scan, re.I):
            result.append({"id": f"C{len(result) + 1:03d}", "text": block})
    return result


def cited_lines(block: str, run_dir: Path, filings: dict[str, Any]) -> list[dict[str, Any]]:
    source_files = {p.name.lower(): p for p in run_dir.glob("*.txt")}
    refs: list[tuple[str | None, list[int]]] = []
    for match in re.finditer(
        r"(?:(?P<file>[A-Za-z0-9_.-]+\.txt)[^\n]*?)?\bline(?:s)?\s+(?P<nums>\d+(?:\s*[-–]\s*\d+)?(?:\s*(?:,|and)\s*\d+(?:\s*[-–]\s*\d+)?)*)",
        block,
        re.I,
    ):
        nums: list[int] = []
        for part in re.findall(r"\d+(?:\s*[-–]\s*\d+)?", match.group("nums")):
            if "-" in part or "–" in part:
                ends = re.split(r"\s*[-–]\s*", part)
                nums.extend(range(int(ends[0]), min(int(ends[-1]), int(ends[0]) + 20) + 1))
            else:
                nums.append(int(part))
        refs.append((match.group("file"), sorted(set(nums))))
    out: list[dict[str, Any]] = []
    for file_name, nums in refs:
        path: Path | None = source_files.get(file_name.lower()) if file_name else None
        if path is None:
            form_match = re.search(r"\b(10-K|10-Q|8-K)\b", block, re.I)
            form = form_match.group(1).upper() if form_match else None
            if form is None and re.search(r"\bItem\s*(?:1|7)(?:\s|\b)", block, re.I):
                form = "10-K"
            if form is None and re.search(r"\|\s*(?:Total revenue|Operating income|Net income|Diluted EPS|Stockholders|Current portion|Long-term debt|Cash from operations|Additions to property)", block, re.I):
                form = "10-K"
            if form == "10-K":
                key = "10-K"
            elif form == "10-Q":
                key = "10-Q"
            elif form == "8-K":
                key = "earnings_8k"
            else:
                key = ""
            info = filings.get(key, {}) if key else {}
            candidate = f"10-K_{info.get('date')}.txt" if key == "10-K" else f"10-Q_{info.get('date')}.txt" if key == "10-Q" else f"8-K_Ex99.1_{info.get('date')}.txt" if key else ""
            path = source_files.get(candidate.lower()) if candidate else None
        if path is None:
            out.append({"filename": file_name or "unresolved", "lines": nums, "valid": False, "excerpts": []})
            continue
        all_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        excerpts = []
        for number in nums:
            if 1 <= number <= len(all_lines):
                excerpts.append({"line": number, "text": all_lines[number - 1]})
            else:
                excerpts.append({"line": number, "text": "", "out_of_range": True})
        out.append({
            "filename": path.name,
            "lines": nums,
            "valid": bool(nums) and all(1 <= n <= len(all_lines) for n in nums),
            "excerpts": excerpts,
        })
    return out


def fact_matches(block: str, run_dir: Path) -> list[dict[str, Any]]:
    all_fact_files = [run_dir / "facts.json"]
    peer_row = re.match(r"\|\s*([A-Z][A-Z0-9.-]{0,7})\s*\|", block)
    if peer_row:
        peer_file = run_dir / f"{peer_row.group(1)}_facts.json"
        if peer_file.exists():
            all_fact_files = [peer_file]
    found: list[dict[str, Any]] = []
    tags = set(re.findall(r"`([A-Za-z][A-Za-z0-9]+)`", block))
    tags.update(re.findall(r"\b([A-Z][A-Za-z]+(?:[A-Z][A-Za-z0-9]+)+)\b", block))
    for path in all_fact_files:
        if not path.exists():
            continue
        try:
            facts = desk_app.read_json(path)
        except Exception:
            continue
        for key, fact in facts.items():
            if not isinstance(fact, dict) or not fact.get("tag") or fact["tag"] not in tags:
                continue
            found.append({"file": path.name, "concept": key, **fact})
    return found


def fact_correction(fact: dict[str, Any], sources: list[dict[str, Any]]) -> str:
    value = fact.get("val")
    if fact.get("unit") == "USD/shares" and isinstance(value, (int, float)):
        shown_value = f"${value:.2f} per share"
    else:
        shown_value = str(value)
    parts = [
        f"Tag `{fact['tag']}` in {fact['file']} records {shown_value} "
        f"for period end {fact.get('end', 'not recorded')}"
    ]
    for source in sources:
        for excerpt in source.get("excerpts", []):
            line_text = excerpt.get("text", "").strip()
            if line_text:
                parts.append(f"{source['filename']}, line {excerpt['line']}: {line_text}")
                return "; ".join(parts) + "."
    return "; ".join(parts) + "."


def amount_tokens(text: str) -> list[float]:
    clean = re.sub(r"\b(?:line|lines|page|pages)\s+\d+(?:\s*[-–]\s*\d+)?", "", text, flags=re.I)
    clean = re.sub(r"\b(?:accession|CIK)\s+\S+", "", clean, flags=re.I)
    clean = re.sub(r"\b(?:FY|fiscal year)\s*20\d{2}\b", "", clean, flags=re.I)
    clean = re.sub(r"\b20\d{2}-\d{2}-\d{2}\b", "", clean)
    global_million = bool(re.search(r"\bmillions?\b", clean, re.I))
    global_billion = bool(re.search(r"\bbillions?\b", clean, re.I))
    vals: list[float] = []
    for match in re.finditer(r"(?<![A-Za-z])\$?\s*(-?\d[\d,]*(?:\.\d+)?)\s*(billion|million|B|M)?(?=\s|[|,.;)]|$)", clean, re.I):
        raw = float(match.group(1).replace(",", ""))
        unit = (match.group(2) or "").lower()
        if unit in ("billion", "b"):
            raw *= 1_000_000_000
        elif unit in ("million", "m"):
            raw *= 1_000_000
        elif not unit and global_billion and abs(raw) < 100_000:
            raw *= 1_000_000_000
        elif not unit and global_million and abs(raw) < 100_000:
            raw *= 1_000_000
        vals.append(raw)
    return vals


def validate_claim_block(block: str, run_dir: Path, filings: dict[str, Any]) -> dict[str, Any]:
    sources = cited_lines(block, run_dir, filings)
    facts = fact_matches(block, run_dir)
    checks: list[str] = []
    forced_mark: str | None = None
    correction = ""
    if not sources and not facts:
        forced_mark = "unsupported"
        checks.append("No filing line or XBRL tag was found in this claim block.")
    for source in sources:
        if not source["valid"]:
            forced_mark = "unsupported"
            checks.append(f"The cited line is not present in {source['filename']}.")
            continue
        checks.append(f"The cited line number exists in {source['filename']}.")
        for excerpt in source["excerpts"]:
            if excerpt.get("out_of_range"):
                forced_mark = "unsupported"
                checks.append(f"Line {excerpt['line']} is outside the saved filing text.")
    quotes = [html.unescape(q) for q in re.findall(r'["“](.+?)["”]', block, re.S)]
    if quotes and sources:
        cited_text = " ".join(
            excerpt.get("text", "")
            for source in sources
            for excerpt in source.get("excerpts", [])
        )
        normalized_source = normalized_quote(cited_text)
        for quote in quotes:
            normalized = normalized_quote(quote)
            if normalized and normalized not in normalized_source:
                forced_mark = "unsupported"
                checks.append("A quoted passage does not match the cited filing line after spacing and formatting normalization.")
                break
    if facts:
        values = amount_tokens(block)
        peer_row = re.match(r"\|\s*([A-Z][A-Z0-9.-]{0,7})\s*\|", block)
        is_peer = bool(peer_row and (run_dir / f"{peer_row.group(1)}_facts.json").exists())
        for fact in facts:
            current = fact.get("val")
            prior = fact.get("prior_val")
            value_index = 1 if fact["concept"].lower() == "operating_income" and is_peer else 0
            matches_current = (
                isinstance(current, (int, float))
                and len(values) > value_index
                and values[value_index] == float(current)
            )
            matches_prior = (
                isinstance(prior, (int, float))
                and len(values) > value_index + 1
                and values[value_index + 1] == float(prior)
            )
            if not is_peer and value_index == 0 and isinstance(prior, (int, float)) and len(values) > 1:
                values_match = matches_current and matches_prior
            else:
                values_match = matches_current
            if (isinstance(current, (int, float)) or isinstance(prior, (int, float))) and not values_match:
                forced_mark = "wrong"
                correction = fact_correction(fact, sources)
                checks.append(f"The printed values do not match tag {fact['tag']} in the saved facts.")
            if current is not None:
                cited_dates = re.findall(r"\b20\d{2}-\d{2}-\d{2}\b", block)
                cited_years = re.findall(r"\b(?:FY|fiscal year)\s*(20\d{2})\b", block, re.I)
                fact_end = fact.get("end")
                fact_year = fact.get("fy")
                if cited_dates and fact_end and fact_end not in cited_dates:
                    forced_mark = "wrong"
                    correction = (
                        f"Tag `{fact['tag']}` in {fact['file']} records {fact.get('val')} "
                        f"for period end {fact_end}."
                    )
                    checks.append(f"The cited period does not match tag {fact['tag']} in the saved facts.")
                elif cited_years and fact_year:
                    cited_year_values = [int(year) for year in cited_years]
                    current_year_ok = cited_year_values[0] == int(fact_year)
                    prior_year_ok = (
                        not isinstance(prior, (int, float))
                        or len(cited_year_values) < 2
                        or cited_year_values[1] == int(fact_year) - 1
                    )
                    if not current_year_ok or not prior_year_ok:
                        forced_mark = "wrong"
                        correction = fact_correction(fact, sources)
                        checks.append(f"The cited fiscal year does not match tag {fact['tag']} in the saved facts.")
                elif not cited_dates and not cited_years:
                    forced_mark = forced_mark or "unsupported"
                    checks.append(f"No period is stated for tag {fact['tag']}.")
    arithmetic_ok, arithmetic_note = arithmetic_result(block)
    definition_ok, definition_note = ratio_definition_result(block)
    if arithmetic_ok is False:
        forced_mark = "wrong"
        correction = (correction + " " + arithmetic_note).strip()
        checks.append(arithmetic_note)
    elif arithmetic_ok is True:
        checks.append(arithmetic_note)
    if definition_ok is False:
        forced_mark = forced_mark or "unsupported"
        checks.append(definition_note)
    elif definition_ok is True:
        checks.append(definition_note)
    return {
        "code_mark": forced_mark,
        "code_checks": checks,
        "correction": correction,
        "sources": sources,
        "facts": facts,
        "arithmetic_check": arithmetic_note,
        "ratio_definition_check": definition_note,
    }


def verifier_evidence(report: str, run_dir: Path, filings: dict[str, Any]) -> list[dict[str, Any]]:
    items = report_blocks(report)
    evidence = []
    for item in items:
        validation = validate_claim_block(item["text"], run_dir, filings)
        evidence.append({**item, **validation})
    return evidence


def related_filing_lines(block: str, run_dir: Path) -> list[dict[str, Any]]:
    """Find saved filing lines that can support a correction for a claim."""
    text = block.lower()
    searches = (
        (("revenue", "sales"), ("total revenue", "net sales", "revenue")),
        (("operating income", "operating margin"), ("operating income",)),
        (("net income", "diluted eps", "earnings per share"), ("net income", "diluted")),
        (("equity", "return on equity"), ("total equity", "stockholders' equity", "equity")),
        (("debt",), ("current portion of long-term debt", "long-term debt")),
        (("cash from operations", "cash flow"), ("net cash provided by operating activities",)),
        (("free cash flow", "capex", "property and equipment"), ("additions to property and equipment", "capital expenditures")),
        (("warehouse", "membership", "members", "competitor", "competition"), ("warehouse", "membership", "competition")),
    )
    terms = [term for triggers, choices in searches if any(trigger in text for trigger in triggers) for term in choices]
    if not terms:
        return []
    results: list[dict[str, Any]] = []
    for path in sorted(run_dir.glob("*.txt")):
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        selected: list[int] = []
        hit_count = 0
        for index, line in enumerate(lines):
            if any(term in line.lower() for term in terms):
                hit_count += 1
                for nearby in range(max(0, index - 1), min(len(lines), index + 2)):
                    if nearby not in selected:
                        selected.append(nearby)
                if hit_count >= 2:
                    break
        if selected:
            results.append({
                "filename": path.name,
                "lines": [{"line": index + 1, "text": lines[index]} for index in selected[:6]],
            })
    return results


def mark_rows(items: list[dict[str, Any]], model_result: dict[str, Any] | None) -> list[dict[str, str]]:
    model_by_id = {
        str(item.get("id")): item
        for item in (model_result or {}).get("items", [])
        if isinstance(item, dict)
    }
    rows: list[dict[str, str]] = []
    for item in items:
        model_item = model_by_id.get(item["id"], {})
        code_mark = item.get("code_mark")
        model_mark = str(model_item.get("mark", "")).strip().lower()
        if model_mark in {"ok", "verified", "supported"}:
            model_mark = "correct"
        if code_mark in {"wrong", "unsupported"}:
            mark = code_mark
        elif model_mark in {"correct", "wrong", "unsupported"}:
            mark = model_mark
        else:
            mark = code_mark or "unsupported"
        reason = "; ".join(item.get("code_checks", []))
        if model_item.get("reason"):
            reason = (reason + "; " + str(model_item["reason"])).strip("; ")
        correction = item.get("correction") or str(model_item.get("correction", ""))
        rows.append({"id": item["id"], "mark": mark, "claim": item["text"], "reason": reason, "correction": correction})
    return rows


def render_verified_report(report: str, rows: list[dict[str, str]], status: str) -> str:
    lines = report.splitlines()
    first = lines[0] if lines else "Filings read: source list unavailable"
    run_time = lines[1] if len(lines) > 1 and lines[1].startswith("Run time:") else "Run time: not recorded"
    body = "\n".join(lines[2:]).lstrip() if len(lines) > 2 else ""
    table = [
        "## Verifier table",
        "",
        f"Verifier model status: {status}",
        "",
        "| ID | Mark | Claim | Finding or correction |",
        "|---|---|---|---|",
    ]
    if not rows:
        table.append("| — | unsupported | No numeric claims were found outside Investment Recommendation. | — |")
    for row in rows:
        claim = row["claim"].replace("|", "\\|").replace("\n", " ")
        finding = (row["reason"] + (" Correction: " + row["correction"] if row["correction"] else "")).replace("|", "\\|").replace("\n", " ")
        table.append(f"| {row['id']} | {row['mark']} | {claim} | {finding} |")
    table_text = "\n".join(table)
    return f"{first}\n\n{table_text}\n\n{run_time}\n\n---\n\n{body}\n"


def run_verifier(state: TeamState) -> dict[str, Any]:
    attempt, counts = start_node(state, "Verifier")
    run_dir = Path(state["run_dir"])
    report_path = Path(state.get("report_path", str(run_dir / "report.md")))
    if not report_path.exists():
        candidates = [run_dir / "report.md", *run_dir.glob("*_equity_research_report.md")]
        report_path = next((p for p in candidates if p.exists()), report_path)
    if not report_path.exists():
        raise FileNotFoundError(f"No report file found in saved run: {run_dir}")
    report = report_path.read_text(encoding="utf-8", errors="replace")
    filings = desk_app.read_json(run_dir / "filings.json")
    evidence = verifier_evidence(report, run_dir, filings)
    facts = desk_app.read_json(run_dir / "facts.json")
    saved_facts = {"facts.json": facts}
    for facts_path in run_dir.glob("*_facts.json"):
        saved_facts[facts_path.name] = desk_app.read_json(facts_path)
    filing_text_evidence = [
        {
            "id": item["id"],
            "text": item["text"],
            "cited_lines": item["sources"],
            "related_saved_filing_lines": related_filing_lines(item["text"], run_dir),
        }
        for item in evidence
    ]
    payload = desk_app.role_payload(
        "Verify every factual and numeric claim outside the Investment Recommendation section. Return exactly one result for every supplied claim ID, in the same order, with no omitted IDs. Do not assess the Investment Advisor's thesis or recommendation. Check only the compiled report, supplied filing text evidence, and supplied saved facts. Mark a claim wrong only when those sources show a different value, period, definition, or arithmetic result. If evidence is missing, mark unsupported, not wrong. Use a price stated in the report to check P/E.",
        {
            "compiled_report": report,
            "saved_filing_texts": filing_text_evidence,
            "saved_facts": saved_facts,
        },
        "One compact JSON object with an items array. Each item has id, mark, reason, and correction. Include every supplied ID exactly once and in the supplied order.",
    )
    save_node_event(run_dir, "Verifier", attempt, payload, {"status": "started"})
    status = "complete"
    model_result: dict[str, Any] | None = None
    try:
        model_result = as_json(call_model("Verifier", payload), "Verifier")
        save_node_event(run_dir, "Verifier", attempt, payload, model_result)
    except Exception as exc:
        status = f"model unavailable: {type(exc).__name__}: {exc}"
        save_node_event(run_dir, "Verifier", attempt, payload, {"error": repr(exc)})
    rows = mark_rows(evidence, model_result)
    verified_report = render_verified_report(report, rows, status)
    verified_path = run_dir / "verified_report.md"
    verified_path.write_text(verified_report, encoding="utf-8")
    save_json(run_dir / "verification_items.json", evidence)
    save_json(run_dir / "verification_marks.json", rows)
    print(f"Verifier status: {status}", flush=True)
    print(f"Saved verified report: {verified_path}", flush=True)
    return {
        "verification_items": evidence,
        "verification_rows": rows,
        "verifier_status": status,
        "node_counts": counts,
    }


def verifier_node(state: TeamState) -> dict[str, Any]:
    return run_verifier(state)


def save_report_node(state: TeamState) -> dict[str, Any]:
    """Save the Manager's compiled report before the mandatory verifier runs."""
    attempt, counts = start_node(state, "Save Report")
    run_dir = Path(state["run_dir"])
    header = desk_app.filing_header(state["ticker"], state["filings"], state.get("peers", []), run_dir)
    report_path = run_dir / "report.md"
    report = f"{header}\nRun time: {state['run_time']}\n\n{state.get('report_body', '').strip()}\n"
    report_path.write_text(report, encoding="utf-8")
    save_json(run_dir / "role_outputs.json", state.get("role_outputs", {}))
    save_json(run_dir / "manager_checks.json", state.get("manager_checks", []))
    save_node_event(run_dir, "Save Report", attempt, {"report_body": state.get("report_body", "")}, {"report_path": str(report_path)})
    return {"report_path": str(report_path), "node_counts": counts}


class DeskTeamFlow(Flow[DeskTeamState]):
    """Fixed CrewAI Flow for the seven-step desk and four role team."""

    # The workflow stores its evidence and state in the run folder. It does not
    # use vector memory, whose native LanceDB dependency is blocked on some
    # managed Windows installations.
    _skip_auto_memory = True

    def state_dict(self) -> TeamState:
        return self.state.model_dump(exclude={"id"})

    def apply(self, updates: dict[str, Any]) -> None:
        for key, value in updates.items():
            if key in DeskTeamState.model_fields:
                setattr(self.state, key, value)

    @start()
    def steps_node(self) -> str:
        self.apply(create_data_steps(self.state_dict()))
        return self.state.run_dir

    @listen(steps_node)
    def research_analyst_node(self, _steps_result: str) -> str:
        self.apply(role_node("Research Analyst")(self.state_dict()))
        return self.state.role_outputs["Research Analyst"]

    @listen(research_analyst_node)
    def financial_analyst_node(self, _research_result: str) -> str:
        self.apply(role_node("Financial Analyst")(self.state_dict()))
        return self.state.role_outputs["Financial Analyst"]

    @listen(financial_analyst_node)
    def investment_advisor_node(self, _financial_result: str) -> str:
        self.apply(run_investment_advisor_node(self.state_dict()))
        return self.state.role_outputs["Investment Advisor"]

    @listen(investment_advisor_node)
    def strategy_manager_flow_node(self, _advisor_result: str) -> str:
        state = self.state_dict()
        first_review = strategy_manager_node(state)
        self.apply(first_review)
        had_revisions = bool(first_review.get("retry_queue"))
        while self.state.retry_queue:
            state = self.state_dict()
            self.apply(retry_dispatch_node(state))
            route = retry_route(self.state_dict())
            role = {
                "retry_research": "Research Analyst",
                "retry_financial": "Financial Analyst",
                "retry_advisor": "Investment Advisor",
            }.get(route)
            if role is None:
                break
            self.apply(retry_role_node(role)(self.state_dict()))
        if had_revisions:
            self.apply(final_compile_node(self.state_dict()))
        saved = save_report_node(self.state_dict())
        self.apply(saved)
        return self.state.report_path

    @listen(strategy_manager_flow_node)
    def verifier_flow_node(self, _report_path: str) -> str:
        self.apply(verifier_node(self.state_dict()))
        return str(Path(self.state.run_dir) / "verified_report.md")


class VerifierOnlyFlow(Flow[DeskTeamState]):
    """Run only the mandatory verifier on a saved run."""

    _skip_auto_memory = True

    def state_dict(self) -> TeamState:
        return self.state.model_dump(exclude={"id"})

    @start()
    def verifier_flow_node(self) -> str:
        run_verifier(self.state_dict())
        return str(Path(self.state.run_dir) / "verified_report.md")


def setup_model() -> None:
    global GLOBAL_MODEL
    env: dict[str, str] = {}
    for line in (BASE / ".env").read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    api_key = env.get("API_KEY", "").strip()
    model = env.get("MODEL", "").strip()
    if not api_key:
        raise RuntimeError(".env must contain API_KEY")
    if not model:
        raise RuntimeError(".env must contain MODEL")
    GLOBAL_MODEL = LLM(
        model=f"openai/{model}",
        api_key=api_key,
        base_url=desk_app.GENAI_BASE_URL,
        timeout=300,
        temperature=0.2,
        max_tokens=6000,
    )


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(description="Run the seven-step desk in a fixed CrewAI Flow and always verify its report.")
    parser.add_argument("ticker", nargs="?", help="Ticker symbol for a new team run")
    parser.add_argument("--peers", default="", help="Comma-separated peer tickers")
    parser.add_argument("--price", type=float, help="Share price used for P/E")
    parser.add_argument("--verify-only", type=Path, help="Verify a saved run folder and do nothing else")
    args = parser.parse_args()
    setup_model()
    if args.verify_only:
        if args.ticker or args.peers or args.price is not None:
            parser.error("--verify-only does not take a ticker, peers, or price")
        run_dir = args.verify_only.resolve()
        if not run_dir.is_dir():
            parser.error(f"Saved run folder does not exist: {run_dir}")
        report_path = run_dir / "report.md"
        if not report_path.exists():
            report_path = next(iter(run_dir.glob("*_equity_research_report.md")), report_path)
        if not report_path.exists():
            parser.error(f"No report.md exists in saved run folder: {run_dir}")
        VerifierOnlyFlow().kickoff(inputs={
            "run_dir": str(run_dir),
            "report_path": str(report_path),
            "node_counts": {},
        })
        return
    if not args.ticker:
        parser.error("ticker is required unless --verify-only is used")
    peers = [peer.strip().upper() for peer in args.peers.split(",") if peer.strip()]
    if args.price is not None and args.price <= 0:
        parser.error("--price must be greater than zero")
    initial = {
        "ticker": args.ticker.upper(),
        "peers": peers,
        "price": args.price,
        "role_payloads": {},
        "role_outputs": {},
        "retry_queue": [],
        "retry_used": {},
        "node_counts": {},
    }
    DeskTeamFlow().kickoff(inputs=initial)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Lab 04 run stopped: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        raise
