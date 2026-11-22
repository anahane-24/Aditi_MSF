"""Find recent Form 10 spinoff candidates on EDGAR and rank declared factors."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

import closes_reader
import desk_steps


BASE = Path(__file__).resolve().parent
EFTS = "https://efts.sec.gov/LATEST/search-index"
ARCHIVES = "https://www.sec.gov/Archives/edgar/data"
DEFAULT_FACTORS = BASE / "config" / "spinoff_factors.json"


def score_rows(rows: list[dict], config: dict) -> list[dict]:
    """Apply only thresholds and weights written in the factor file."""
    factors = config.get("factors", [])
    if not factors:
        raise ValueError("The hand-written factor file has no factors yet.")
    for factor in factors:
        if not factor.get("name") or not factor.get("field") or not factor.get("source_chapter"):
            raise ValueError("Each hand-written factor needs name, field, and source_chapter.")
        if factor.get("direction") not in {"higher", "lower"}:
            raise ValueError(f"Factor {factor['name']} needs direction 'higher' or 'lower'.")
        if not isinstance(factor.get("weight"), (int, float)) or not isinstance(factor.get("threshold"), (int, float)):
            raise ValueError(f"Factor {factor['name']} needs a numeric weight and threshold written by the student.")
    if not isinstance(config.get("window_days"), int) or config["window_days"] < 1:
        raise ValueError("The hand-written factor file needs window_days, an integer greater than zero.")
    results = []
    for row in rows:
        scores = []
        missing = []
        for factor in factors:
            value = row.get("features", {}).get(factor["field"])
            if not isinstance(value, (int, float)):
                missing.append(factor["name"])
                scores.append({"factor": factor["name"], "value": value, "points": None})
                continue
            meets = value >= factor["threshold"] if factor["direction"] == "higher" else value <= factor["threshold"]
            points = float(factor["weight"]) if meets else 0.0
            scores.append({"factor": factor["name"], "value": value, "points": points})
        result = dict(row)
        result["factor_scores"] = scores
        result["ranked"] = not missing
        result["unranked_reason"] = "Missing data for: " + ", ".join(missing) if missing else None
        result["total_points"] = sum(item["points"] or 0 for item in scores) if not missing else None
        results.append(result)
    return sorted(results, key=lambda item: (item["ranked"], item["total_points"] or 0), reverse=True)


def query_candidates(start_date: str, end_date: str, ua: str) -> list[dict]:
    hits: list[dict] = []
    offset = 0
    while True:
        params = {
            "q": '"information statement" distribution',
            "forms": "10-12B,10-12G",
            "startdt": start_date,
            "enddt": end_date,
            "from": str(offset),
            "size": "100",
        }
        data = desk_steps.json_get(EFTS + "?" + urlencode(params), ua)
        page = data.get("hits", {}).get("hits", [])
        hits.extend(item.get("_source", {}) for item in page)
        total = int(data.get("hits", {}).get("total", {}).get("value", len(hits)))
        offset += len(page)
        if not page or offset >= total:
            break
    return hits


def filing_text(hit: dict, ua: str) -> tuple[str, str]:
    cik = str((hit.get("ciks") or [""])[0]).zfill(10)
    accession = str(hit.get("adsh", ""))
    if not cik.strip("0") or not accession:
        return "", "missing CIK or accession in EDGAR search result"
    folder = accession.replace("-", "")
    index_url = f"{ARCHIVES}/{int(cik)}/{folder}/index.json"
    try:
        index = desk_steps.json_get(index_url, ua)
        files = index.get("directory", {}).get("item", [])
        primary = next((item["name"] for item in files if item.get("name", "").lower().endswith((".htm", ".html")) and "-index" not in item["name"].lower() and "ex" not in item["name"].lower()), None)
        if not primary:
            return "", "EDGAR index did not show a primary HTML document"
        raw = desk_steps.get(f"{ARCHIVES}/{int(cik)}/{folder}/{primary}", ua)
        return desk_steps.plain_text(raw), primary
    except Exception as exc:
        return "", f"EDGAR document could not be read: {type(exc).__name__}: {exc}"


def date_from_text(text: str) -> str | None:
    patterns = (
        r"(?:distribution|spin-off|spinoff) date(?: is|:| of)?\s+([A-Z][a-z]+\s+\d{1,2},\s+20\d{2})",
        r"(?:distribution|spin-off|spinoff) date(?: is|:| of)?\s+(20\d{2}-\d{2}-\d{2})",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            value = match.group(1)
            for fmt in ("%B %d, %Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(value, fmt).date().isoformat()
                except ValueError:
                    pass
    return None


def evidence_snippets(text: str) -> list[str]:
    lines = text.splitlines()
    return [line.strip() for line in lines if re.search(r"information statement|distribution date|distribute.*share|shares.*distribute|parent company", line, re.I)][:12]


def make_registry(start_date: str, end_date: str, ua: str, env: dict[str, str], window_days: int | None) -> tuple[list[dict], list[dict]]:
    hits = query_candidates(start_date, end_date, ua)
    accepted, dropped = [], []
    seen = set()
    for hit in hits:
        accession = str(hit.get("adsh", ""))
        if not accession or accession in seen:
            continue
        seen.add(accession)
        text, document = filing_text(hit, ua)
        form = str(hit.get("form", hit.get("file_type", "")))
        entity = str((hit.get("display_names") or ["Unknown filer"])[0]).split(" (CIK")[0]
        has_statement = bool(re.search(r"information statement", text, re.I))
        has_distribution = bool(re.search(r"distribut\w{0,5}.{0,100}(?:shares|stock)|(?:shares|stock).{0,100}distribut\w{0,5}", text, re.I | re.S))
        reason = None
        if not text:
            reason = document
        elif not has_statement:
            reason = "Form 10 filing text does not identify an information statement."
        elif not has_distribution:
            reason = "No parent-to-holder share distribution evidence was found in the primary document."
        row = {
            "filer": entity,
            "cik": str((hit.get("ciks") or [""])[0]).zfill(10),
            "form": form,
            "filed": hit.get("file_date"),
            "accession": accession,
            "document": document if not reason else None,
            "distribution_date": date_from_text(text),
            "evidence": evidence_snippets(text),
            "classification": "candidate for hand review" if not reason else "dropped",
            "drop_reason": reason,
            "features": {},
        }
        if reason:
            dropped.append(row)
            continue
        dist = row["distribution_date"]
        if dist and window_days:
            ticker = ticker_for_cik(row["cik"], ua)
            row["ticker"] = ticker
            if ticker:
                start = date.fromisoformat(dist)
                end = min(start + timedelta(days=window_days), date.fromisoformat(end_date))
                closes = closes_reader.closes_between(ticker, start.isoformat(), end.isoformat(), env)
                if closes:
                    first, last = closes[0].value, closes[-1].value
                    row["features"]["window_return"] = (last / first) - 1 if first else None
                    row["price_start"] = {"date": closes[0].date, "close": first, "source": closes[0].source}
                    row["price_end"] = {"date": closes[-1].date, "close": last, "source": closes[-1].source}
                else:
                    row["features"]["window_return"] = None
        accepted.append(row)
    return accepted, dropped


def ticker_for_cik(cik: str, ua: str) -> str | None:
    try:
        payload = desk_steps.json_get("https://www.sec.gov/files/company_tickers.json", ua)
        for row in payload.values():
            if str(row.get("cik_str", "")).zfill(10) == cik:
                return str(row.get("ticker", "")).upper() or None
    except Exception:
        return None
    return None


def write_report(path: Path, start_date: str, end_date: str, candidates: list[dict], dropped: list[dict], factor_error: str | None) -> None:
    output = [f"Screen run: {datetime.now().astimezone().isoformat(timespec='seconds')} | price through: {end_date} | EDGAR index date: {end_date}", "", "## Candidates for hand review", ""]
    if factor_error:
        output.append(f"Ranking not run: {factor_error}")
        output.append("")
    if not candidates:
        output.append("No Form 10 candidates matched this search window.")
    else:
        output.extend(["| Filer | Ticker | Filed | Distribution date | Points | Factor points / missing data | Filing |", "|---|---|---|---|---:|---|---|"])
        for row in candidates:
            scores = "; ".join(f"{s['factor']}: {s['points'] if s['points'] is not None else 'not available'}" for s in row.get("factor_scores", [])) or "Not ranked; factors are not configured."
            link = f"https://www.sec.gov/Archives/edgar/data/{int(row['cik'])}/{row['accession'].replace('-', '')}/{row.get('document') or ''}"
            output.append(f"| {row['filer']} | {row.get('ticker') or 'not available'} | {row.get('filed') or 'unknown'} | {row.get('distribution_date') or 'not found'} | {row.get('total_points') if row.get('ranked') else 'unranked'} | {scores} | [Form 10]({link}) |")
            if row.get("unranked_reason"):
                output.append(f"| Data gap | | | | | {row['unranked_reason']} | |")
    output.extend(["", "## Watch list", "", "No confirmed pre-distribution registrants are classified automatically. Review the Form 10 evidence before adding a name.", "", "## Dropped filings", ""])
    if dropped:
        for row in dropped:
            output.append(f"- {row['filer']} — {row['form']} filed {row.get('filed')}; dropped: {row['drop_reason']} Accession {row['accession']}.")
    else:
        output.append("None.")
    output.extend(["", "Facts that the filing or price source did not establish remain unavailable. Each candidate requires a filing review.", "", "screens, not recommendations"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(output) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Search EDGAR Form 10 filings for U.S. spinoff candidates.")
    parser.add_argument("--start", required=True, help="Start date, YYYY-MM-DD")
    parser.add_argument("--end", default=date.today().isoformat(), help="End date, YYYY-MM-DD")
    parser.add_argument("--factors", type=Path, default=DEFAULT_FACTORS)
    parser.add_argument("--out", type=Path, default=BASE / "screens" / "latest")
    args = parser.parse_args()
    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    if end < start:
        parser.error("--end must be on or after --start")
    env = desk_steps.read_env(BASE / ".env")
    config = json.loads(args.factors.read_text(encoding="utf-8"))
    window_days = config.get("window_days") if isinstance(config.get("window_days"), int) else None
    print("SEEKER: search EDGAR Form 10 filings", flush=True)
    candidates, dropped = make_registry(start.isoformat(), end.isoformat(), env["SEC_USER_AGENT"], env, window_days)
    factor_error = None
    try:
        ranked = score_rows(candidates, config)
    except ValueError as exc:
        factor_error = str(exc)
        ranked = candidates
    for row in ranked:
        if row.get("ranked") is False:
            row["total_points"] = None
    stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    out = args.out / stamp
    out.mkdir(parents=True, exist_ok=False)
    registry = {"start_date": start.isoformat(), "end_date": end.isoformat(), "candidates": ranked, "dropped": dropped, "factor_file": str(args.factors), "ranking_error": factor_error}
    (out / "registry.json").write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(out / "screen.md", start.isoformat(), end.isoformat(), ranked, dropped, factor_error)
    print(f"Saved screen: {out / 'screen.md'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Seeker stopped: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
