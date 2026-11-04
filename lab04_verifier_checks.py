"""Run the deterministic Lab 04 Verifier checks on saved COST test folders."""

from pathlib import Path

import agent_team
import desk_app


BASE = Path(__file__).resolve().parent
TEST_ROOT = BASE / "data" / "Lab04_Verifier_Tests"


def case(name: str) -> tuple[Path, str, dict]:
    folder = TEST_ROOT / name
    report = (folder / "report.md").read_text(encoding="utf-8")
    filings = desk_app.read_json(folder / "filings.json")
    return folder, report, filings


def main() -> None:
    parsed = agent_team.as_json(
        '{"item_id":"C001","mark":"OK"} {"item_id":"C002","mark":"correct"}',
        "Verifier test",
    )
    assert [item["id"] for item in parsed["items"]] == ["C001", "C002"], parsed
    normalized = agent_team.mark_rows(
        [{"id": "C001", "text": "claim", "code_mark": None, "code_checks": [], "correction": ""}],
        {"items": [{"id": "C001", "mark": "OK", "reason": "supported"}]},
    )
    assert normalized[0]["mark"] == "correct", normalized
    print("PASS: adjacent model JSON objects parse, and the endpoint's OK mark normalizes to correct.")

    eps_folder, eps_report, eps_filings = case("eps_plus_1")
    eps_claim = next(
        block["text"]
        for block in agent_team.report_blocks(eps_report)
        if "EarningsPerShareDiluted" in block["text"]
    )
    eps_result = agent_team.validate_claim_block(eps_claim, eps_folder, eps_filings)
    assert eps_result["code_mark"] == "wrong", eps_result
    assert "EarningsPerShareDiluted" in eps_result["correction"], eps_result
    assert "10-K_2026-10-07.txt, line 652" in eps_result["correction"], eps_result
    assert "$20.76 per share" in eps_result["correction"], eps_result
    eps_marks = desk_app.read_json(eps_folder / "verification_marks.json")
    eps_mark = next(mark for mark in eps_marks if "EarningsPerShareDiluted" in mark["claim"])
    assert eps_mark["mark"] == "wrong", eps_mark
    assert "EarningsPerShareDiluted" in eps_mark["correction"], eps_mark
    assert "line 652" in eps_mark["correction"], eps_mark
    print("PASS: seeded +$1 diluted EPS error is marked wrong and corrected from saved XBRL facts.")

    growth_folder, growth_report, growth_filings = case("revenue_growth_plus_4pp")
    growth_claim = next(
        block["text"]
        for block in agent_team.report_blocks(growth_report)
        if "14.1437%" in block["text"]
    )
    growth_result = agent_team.validate_claim_block(growth_claim, growth_folder, growth_filings)
    assert growth_result["code_mark"] == "wrong", growth_result
    assert "recalculated" in growth_result["correction"].lower(), growth_result
    growth_marks = desk_app.read_json(growth_folder / "verification_marks.json")
    growth_mark = next(mark for mark in growth_marks if "14.1437%" in mark["claim"])
    assert growth_mark["mark"] == "wrong", growth_mark
    assert "recalculated" in growth_mark["correction"].lower(), growth_mark
    print("PASS: seeded +4 percentage-point revenue-growth error is marked wrong by arithmetic.")

    clean_folder, clean_report, clean_filings = case("clean_11_core")
    blocks = agent_team.report_blocks(clean_report)
    facts = desk_app.read_json(clean_folder / "facts.json")
    tag_names = {fact.get("tag") for fact in facts.values() if isinstance(fact, dict)}
    fact_blocks = [
        block for block in blocks
        if "FY2026" in block["text"]
        and "FY2025" in block["text"]
        and any(f"`{tag}`" in block["text"] for tag in tag_names if tag)
    ]
    core = blocks[:2] + fact_blocks
    assert len(fact_blocks) == 9, f"Expected 9 annual XBRL facts; found {len(fact_blocks)}"
    assert len(core) == 11, f"Expected 11 core claims; found {len(core)}"
    results = [
        agent_team.validate_claim_block(block["text"], clean_folder, clean_filings)
        for block in core
    ]
    bad = [result for result in results if result["code_mark"] in {"wrong", "unsupported"}]
    assert not bad, bad
    clean_marks = desk_app.read_json(clean_folder / "verification_marks.json")
    mark_by_id = {item["id"]: item["mark"] for item in clean_marks}
    core_ids = [block["id"] for block in core]
    noncorrect = {item_id: mark_by_id.get(item_id) for item_id in core_ids if mark_by_id.get(item_id) != "correct"}
    assert not noncorrect, noncorrect
    print("PASS: all 11 core claims have no deterministic wrong or unsupported marks.")

    graph_path = agent_team.DeskTeamFlow().plot("lab04_flow.html", show=False)
    assert Path(graph_path).is_file(), graph_path
    print("PASS: the current CrewAI Flow graph constructs and plots.")

    for role in ("Research Analyst", "Financial Analyst", "Investment Advisor", "Strategy Manager", "Verifier"):
        try:
            agent_team.start_node({"node_counts": {role: 2}}, role)
        except RuntimeError:
            continue
        raise AssertionError(f"{role} accepted a third call")
    print("PASS: the per-role two-call ceiling is enforced.")


if __name__ == "__main__":
    main()
