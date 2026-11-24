"""Single-command pipeline for the SEC desk, worksheet, and evidence hook."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import desk_app
import evidence_hook
import source_report
import worksheet


BASE = Path(__file__).resolve().parent


def run_command(command: list[str], part: str) -> str:
    print(f"PART: {part}", flush=True)
    started = time.perf_counter()
    result = subprocess.run(command, cwd=BASE, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.stdout:
        print(result.stdout, end="", flush=True)
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr, flush=True)
    if result.returncode:
        raise RuntimeError(f"{part} stopped with exit code {result.returncode}")
    print(f"TIME: {part} {time.perf_counter() - started:.2f} seconds", flush=True)
    return result.stdout


def find_run_dir(output: str) -> Path:
    match = re.search(r"Saved primary-company filings and facts to:\s*(.+)", output)
    if not match:
        raise RuntimeError("Agent team did not print its saved run folder")
    path = Path(match.group(1).strip()).resolve()
    try:
        path.relative_to((BASE / "data").resolve())
    except ValueError as exc:
        raise RuntimeError("Agent team run folder is outside data/") from exc
    if not path.is_dir():
        raise FileNotFoundError(f"Agent team run folder does not exist: {path}")
    return path


def check_screen_registry(path: Path) -> dict[str, Any]:
    registry = json.loads(path.read_text(encoding="utf-8"))
    rows = registry.get("candidates", [])
    problems = []
    for row in rows:
        if row.get("ranked"):
            score_sum = sum(float(item["points"]) for item in row.get("factor_scores", []))
            if abs(score_sum - float(row.get("total_points", 0))) > 1e-9:
                problems.append(f"{row.get('accession')}: factor total does not match points")
            if not row.get("accession") or not row.get("evidence"):
                problems.append(f"{row.get('accession', 'unknown')}: missing filing evidence")
    return {"status": "refused" if problems else "passed", "candidate_count": len(rows), "problems": problems}


def run_team(ticker: str, peers: list[str], filed: str | None) -> tuple[Path, float]:
    command = [sys.executable, str(BASE / "agent_team.py"), ticker]
    if peers:
        command.extend(["--peers", ",".join(peers)])
    if filed:
        command.extend(["--filed", filed])
    started = time.perf_counter()
    output = run_command(command, "Agent team")
    return find_run_dir(output), time.perf_counter() - started


def make_joined_report(run_dir: Path, worksheet_text: str) -> Path:
    source = run_dir / "report.md"
    if not source.is_file():
        raise FileNotFoundError(f"Missing manager report: {source}")
    report = source.read_text(encoding="utf-8")
    report += "\n\n## Worksheet view\n\n" + worksheet_text.strip() + "\n"
    target = run_dir / "joined_report.md"
    target.write_text(report, encoding="utf-8")
    return target


def run_final_checks(run_dir: Path, report_path: Path) -> dict[str, Any]:
    final_hook = evidence_hook.check_report(report_path, run_dir)
    final_worksheet = evidence_hook.check_worksheet(run_dir)
    final_hook["worksheet"] = final_worksheet
    if final_worksheet["mark"] == "refused":
        final_hook["refused"] += 1
    final_verifier = evidence_hook.check_verifier_marks(run_dir)
    final_hook["verifier_marks"] = final_verifier
    if final_verifier["mark"] == "refused":
        final_hook["refused"] += 1
    return final_hook


def run_replay(run_dir: Path) -> int:
    """Check an existing final report without making any network or model calls."""
    report = run_dir / "desk_final_report.md"
    if not report.is_file() and (run_dir / "joined_report.md").is_file():
        report = run_dir / "joined_report.md"
    if not report.is_file():
        raise FileNotFoundError("Saved run has no desk_final_report.md to replay")
    print("PART: Offline replay (no SEC, LSEG, or model calls)", flush=True)
    result = evidence_hook.check_report(report, run_dir)
    worksheet_result = evidence_hook.check_worksheet(run_dir)
    result["worksheet"] = worksheet_result
    result["refused"] += int(worksheet_result["mark"] == "refused")
    verifier_result = evidence_hook.check_verifier_marks(run_dir)
    result["verifier_marks"] = verifier_result
    result["refused"] += int(verifier_result["mark"] == "refused")
    (run_dir / "replay_hook_marks.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Replay hook: {result['passed']} passed; {result['refused']} refused")
    print(f"Saved replay marks: {run_dir / 'replay_hook_marks.json'}")
    print(f"Saved final report: {report}")
    return 1 if result["refused"] else 0


def run_pipeline(ticker: str, peers: list[str], filed: str | None, screen_start: str | None) -> int:
    started = time.perf_counter()
    screen_artifacts: dict[str, str] = {}
    if ticker.lower() == "screen":
        if not screen_start:
            raise ValueError("The screen command needs --start YYYY-MM-DD")
        screen_output = run_command([
            sys.executable, str(BASE / "spinoff_seeker.py"), "--start", screen_start,
        ], "Spinoff seeker")
        match = re.search(r"Saved screen:\s*(.+)", screen_output)
        if not match:
            raise RuntimeError("Seeker did not print its report path")
        screen_path = Path(match.group(1).strip()).resolve()
        registry_path = screen_path.with_name("registry.json")
        screen_check = check_screen_registry(registry_path)
        if screen_check["status"] != "passed":
            raise RuntimeError("Seeker hook refused: " + "; ".join(screen_check["problems"]))
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        ranked = [row for row in registry.get("candidates", []) if row.get("ranked") and row.get("ticker")]
        if not ranked:
            raise RuntimeError("Screen has no fully ranked candidate. Complete the hand-written factor file and its required data first.")
        ticker = str(ranked[0]["ticker"]).upper()
        screen_artifacts = {"screen.md": str(screen_path), "screen_registry.json": str(registry_path)}
        print(f"PICK: {ticker} from the latest screen", flush=True)

    run_dir, team_seconds = run_team(ticker, peers, filed)
    if screen_artifacts:
        for name, source in screen_artifacts.items():
            shutil.copy2(source, run_dir / name)
    timing: dict[str, float] = {"agent_team_seconds": team_seconds}

    print("PART: Evidence hook on agent-team output", flush=True)
    hook_start = time.perf_counter()
    team_hook = evidence_hook.check_report(run_dir / "verified_report.md", run_dir)
    verifier_hook = evidence_hook.check_verifier_marks(run_dir)
    team_hook["verifier_marks"] = verifier_hook
    team_hook["refused"] += int(verifier_hook["mark"] == "refused")
    (run_dir / "team_hook_marks.json").write_text(json.dumps(team_hook, indent=2, ensure_ascii=False), encoding="utf-8")
    timing["team_hook_seconds"] = time.perf_counter() - hook_start
    print(f"Evidence hook: {team_hook['passed']} passed; {team_hook['refused']} refused", flush=True)
    print("PART: Worksheet from saved run", flush=True)
    worksheet_start = time.perf_counter()
    worksheet_text, worksheet_result = worksheet.build_worksheet(run_dir, worksheet.DEFAULT_POLICY)
    timing["worksheet_seconds"] = time.perf_counter() - worksheet_start
    print(f"Saved worksheet: {run_dir / 'worksheet_output.md'}", flush=True)
    worksheet_hook = evidence_hook.check_worksheet(run_dir)
    (run_dir / "worksheet_hook_marks.json").write_text(json.dumps(worksheet_hook, indent=2), encoding="utf-8")
    print(f"Worksheet hook: {worksheet_hook['mark']}", flush=True)
    if worksheet_result["status"] != "complete" or worksheet_hook["mark"] != "passed":
        raise RuntimeError(f"Worksheet stopped. See {run_dir / 'worksheet_output.md'} and complete or reconcile the hand-written inputs.")

    joined_path = make_joined_report(run_dir, worksheet_text)
    run_command([
        sys.executable, str(BASE / "agent_team.py"), "--verify-only", str(run_dir), "--report", str(joined_path),
    ], "Verifier on joined report")
    final_path = run_dir / "verified_report.md"
    final_report = run_dir / "desk_final_report.md"
    shutil.copy2(final_path, final_report)
    print("PART: Final evidence hook", flush=True)
    final_hook = run_final_checks(run_dir, final_report)
    (run_dir / "final_hook_marks.json").write_text(json.dumps(final_hook, indent=2, ensure_ascii=False), encoding="utf-8")
    if final_hook["refused"]:
        print("PART: Source-backed correction", flush=True)
        source_path = source_report.write_source_report(run_dir, ticker, peers)
        source_joined = run_dir / "source_corrected_joined_report.md"
        source_joined.write_text(
            source_path.read_text(encoding="utf-8").rstrip()
            + "\n\n## Worksheet view\n\n"
            + worksheet_text.strip()
            + "\n",
            encoding="utf-8",
        )
        run_command([
            sys.executable,
            str(BASE / "agent_team.py"),
            "--verify-only",
            str(run_dir),
            "--report",
            str(source_joined),
        ], "Verifier on source-backed correction")
        shutil.copy2(run_dir / "verified_report.md", final_report)
        final_hook = run_final_checks(run_dir, final_report)
        (run_dir / "final_hook_marks.json").write_text(
            json.dumps(final_hook, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    timing["total_seconds"] = time.perf_counter() - started
    (run_dir / "part_timings.json").write_text(json.dumps(timing, indent=2), encoding="utf-8")
    print(f"Final evidence hook: {final_hook['passed']} passed; {final_hook['refused']} refused", flush=True)
    if final_hook["refused"]:
        raise RuntimeError(f"Final evidence hook refused the joined report. See {run_dir / 'final_hook_marks.json'}")
    print(f"TIME: Full desk {timing['total_seconds']:.2f} seconds", flush=True)
    print(f"Saved verified report: {final_report}", flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the agent team, worksheet, and evidence hook in fixed code order.")
    parser.add_argument("ticker", nargs="?", help="Ticker symbol or 'screen'")
    parser.add_argument("--peers", default="", help="Comma-separated peer tickers")
    parser.add_argument("--filed", help="Eastern filing time override YYYY-MM-DDTHH:MM:SS")
    parser.add_argument("--start", help="EDGAR screen start date, YYYY-MM-DD; required with screen")
    parser.add_argument("--replay", type=Path, help="Recheck a saved final report without network or model calls")
    args = parser.parse_args()
    if args.replay:
        if args.ticker or args.peers or args.filed or args.start:
            parser.error("--replay cannot be combined with a ticker, peers, filed time, or start date")
        return run_replay(args.replay.resolve())
    if not args.ticker:
        parser.error("Give a ticker, 'screen', or --replay RUN_FOLDER")
    peers = [item.strip().upper() for item in args.peers.split(",") if item.strip()]
    if args.ticker.upper() in peers:
        parser.error("The target ticker cannot also be a peer")
    if args.ticker.lower() != "screen" and args.start:
        parser.error("--start is only used with screen")
    return run_pipeline(args.ticker.upper(), peers, args.filed, args.start)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"DESK STOPPED: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        raise
