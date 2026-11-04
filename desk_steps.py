"""Seven-step, ticker-driven EDGAR research workflow for FIN 67110 Lab 02."""

from __future__ import annotations

import argparse
import html
import json
import re
import time
from http.client import RemoteDisconnected
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


BASE = Path(__file__).resolve().parent
SEC = "https://www.sec.gov"
DATA = "https://data.sec.gov"


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        raise FileNotFoundError(f"Missing {path.name}; create it with SEC_USER_AGENT=Your Name your@email")
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    if not values.get("SEC_USER_AGENT"):
        raise ValueError(".env must contain SEC_USER_AGENT with your name and email")
    return values


def get(url: str, user_agent: str) -> bytes:
    import gzip
    last_error = None
    for attempt in range(4):
        req = Request(url, headers={"User-Agent": user_agent, "Accept-Encoding": "gzip"})
        try:
            with urlopen(req, timeout=45) as response:
                raw = response.read()
                return gzip.decompress(raw) if response.headers.get("Content-Encoding") == "gzip" else raw
        except (HTTPError, URLError, TimeoutError, RemoteDisconnected, ConnectionError) as exc:
            last_error = exc
            if isinstance(exc, HTTPError) and exc.code not in (429, 500, 502, 503, 504):
                break
            time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(f"SEC request failed for {url}: {last_error}") from last_error


def json_get(url: str, user_agent: str) -> dict:
    return json.loads(get(url, user_agent).decode("utf-8"))


def plain_text(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
    text = re.sub(r"(?i)<br\s*/?>|</(?:tr|p|div|h[1-6]|li|section|article)\s*>", "\n", text)
    text = re.sub(r"(?i)</t[dh]\s*>", " | ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t\xa0]+", " ", text)
    text = re.sub(r"\s*\n\s*", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def resolve_ticker(ticker: str, ua: str) -> tuple[str, str]:
    rows = json_get("https://www.sec.gov/files/company_tickers.json", ua)
    ticker = ticker.upper()
    for row in rows.values():
        if row.get("ticker", "").upper() == ticker:
            return str(row["cik_str"]).zfill(10), row["title"]
    raise ValueError(f"Ticker {ticker} was not found in SEC company_tickers.json")


def recent_filings(cik: str, ua: str) -> dict[str, dict]:
    data = json_get(f"{DATA}/submissions/CIK{cik}.json", ua)
    recent = data["filings"]["recent"]
    found: dict[str, dict] = {}
    for i, form in enumerate(recent["form"]):
        if form not in ("10-K", "10-Q", "8-K"):
            continue
        accn = recent["accessionNumber"][i]
        found.setdefault(form, {
            "form": form,
            "date": recent["filingDate"][i],
            "report_date": recent["reportDate"][i],
            "accession": accn,
            "accession_nodash": accn.replace("-", ""),
            "primary_document": recent["primaryDocument"][i],
            "primary_description": recent.get("primaryDocDescription", [""] * len(recent["form"]))[i],
            "accepted_datetime": recent.get("acceptanceDateTime", [""] * len(recent["form"]))[i],
            "cik": cik,
        })
    return found


def filing_index(filing: dict, ua: str) -> str:
    url = f"{SEC}/Archives/edgar/data/{int(filing['cik'])}/{filing['accession_nodash']}/{filing['accession']}-index.htm"
    return plain_text(get(url, ua))


def accepted_time(index_text: str, filing: dict) -> str:
    # The filing detail page shows Accepted in the SEC's local time zone.
    m = re.search(r"Accepted\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})", index_text, re.I)
    if m:
        return f"{m.group(1)} {m.group(2)} (SEC filing page local time)"
    # Support older index formats that show a compact timestamp.
    m = re.search(r"Accepted\s+(\d{14})", index_text, re.I)
    if m:
        stamp = m.group(1)
        return f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]} {stamp[8:10]}:{stamp[10:12]}:{stamp[12:14]} UTC"
    return f"Not shown on directory index (filing date {filing['date']})"


def find_earnings_8k(cik: str, ua: str) -> dict:
    data = json_get(f"{DATA}/submissions/CIK{cik}.json", ua)
    recent = data["filings"]["recent"]
    older = data["filings"].get("files", [])
    entries = [recent]
    for file in older:
        entries.append(json_get(f"{DATA}/submissions/{file['name']}", ua))
    candidates = []
    for batch in entries:
        for i, form in enumerate(batch["form"]):
            desc = batch.get("primaryDocDescription", [""] * len(batch["form"]))[i] or ""
            if form == "8-K":
                candidates.append((batch["filingDate"][i], batch, i, desc))
    candidates.sort(key=lambda x: (x[0], x[1]["accessionNumber"][x[2]]), reverse=True)
    # Newest filings are usually in the recent submission file. Try those first
    # and favor descriptions that identify an earnings release. Fall back to the
    # archived batches only if needed.
    candidates.sort(key=lambda x: (x[0], x[1]["accessionNumber"][x[2]]), reverse=True)
    recent_candidates = [c for c in candidates if c[1] is recent]
    older_candidates = [c for c in candidates if c[1] is not recent]
    def likely_earnings(item: tuple) -> tuple:
        desc = item[3].lower()
        return (not any(word in desc for word in ("earning", "results", "quarterly", "annual", "press release")), -int(item[0].replace("-", "")))
    candidates = sorted(recent_candidates, key=likely_earnings) + older_candidates
    for date, batch, i, desc in candidates:
        accn = batch["accessionNumber"][i]
        filing = {"form": "8-K", "date": date, "report_date": batch["reportDate"][i],
                  "accession": accn, "accession_nodash": accn.replace("-", ""),
                  "primary_document": batch["primaryDocument"][i], "primary_description": desc,
                  "accepted_datetime": batch.get("acceptanceDateTime", [""] * len(batch["form"]))[i], "cik": cik}
        index_url = f"{SEC}/Archives/edgar/data/{int(cik)}/{filing['accession_nodash']}/index.json"
        listing = json_get(index_url, ua)
        docs = listing.get("directory", {}).get("item", [])
        primary = next((x["name"] for x in docs if x["name"].lower() == filing["primary_document"].lower()), filing["primary_document"])
        filing["primary_document"] = primary
        print(f"  Checking 8-K {date} ({filing['accession']}) for Item 2.02")
        body = plain_text(get(f"{SEC}/Archives/edgar/data/{int(cik)}/{filing['accession_nodash']}/{quote(primary)}", ua))
        if re.search(r"Item\s+2\.02", body, re.I):
            exhibit = next((x["name"] for x in docs if re.search(r"(?:ex(?:hibit)?[-_ ]?99[-_. ]?1|99[-_. ]?1|ex99\d)", x["name"], re.I)), None)
            if not exhibit:
                continue
            filing["exhibit_99_1"] = exhibit
            filing["earnings_text"] = plain_text(get(f"{SEC}/Archives/edgar/data/{int(cik)}/{filing['accession_nodash']}/{quote(exhibit)}", ua))
            return filing
        time.sleep(0.12)
    raise RuntimeError("No 8-K with Item 2.02 and Exhibit 99.1 was found")


TAG_CANDIDATES = {
    "total_revenue": ["Revenues", "SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax", "RevenueFromContractWithCustomerExcludingAssessedTax"],
    "operating_income": ["OperatingIncomeLoss"],
    "net_income": ["NetIncomeLoss"],
    "diluted_eps": ["EarningsPerShareDiluted"],
    "equity": ["StockholdersEquity"],
    "long_term_debt": ["LongTermDebtNoncurrent", "LongTermDebt"],
    "current_debt": ["LongTermDebtCurrent"],
    "cash_from_operations": ["NetCashProvidedByUsedInOperatingActivities"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
}


def get_facts(cik: str, ua: str, filing: dict) -> dict[str, dict]:
    data = json_get(f"{DATA}/api/xbrl/companyfacts/CIK{cik}.json", ua)["facts"]["us-gaap"]
    fy_end = filing.get("report_date") or filing["date"]
    # Pick a revenue fact for the filing's fiscal year, then use that year end
    # to keep every other concept on a consistent period.
    rev_rows = []
    for tag in TAG_CANDIDATES["total_revenue"]:
        if tag not in data:
            continue
        for unit, rows in data[tag]["units"].items():
            for row in rows:
                if row.get("form") == "10-K" and row.get("filed", "") <= filing["date"] and row.get("end", "") <= fy_end and row.get("fp") == "FY" and row.get("start"):
                    rev_rows.append((row.get("end", ""), row.get("filed", ""), tag, unit, row))
    if not rev_rows:
        raise RuntimeError("Could not find annual revenue facts for the latest 10-K")
    latest_end = max(r[0] for r in rev_rows)
    # At a chosen period end, prefer a total-revenue concept over a net-sales-only concept.
    chosen_rev = next((r for r in sorted(rev_rows, key=lambda x: (x[0], x[1]), reverse=True) if r[0] == latest_end), None)
    fy = chosen_rev[4].get("fy")
    results: dict[str, dict] = {}
    for name, tags in TAG_CANDIDATES.items():
        matches = []
        for tag in tags:
            if tag not in data:
                continue
            for unit, rows in data[tag]["units"].items():
                for row in rows:
                    if row.get("end") != latest_end or row.get("form") != "10-K" or row.get("filed", "") > filing["date"]:
                        continue
                    if row.get("fp") == "FY" or row.get("fy") == fy:
                        matches.append((row.get("filed", ""), tag, unit, row))
        if name == "total_revenue":
            results[name] = {"tag": chosen_rev[2], "unit": chosen_rev[3], **chosen_rev[4]}
        elif matches:
            pick = max(matches, key=lambda x: (x[0], tags.index(x[1]) * -1))
            results[name] = {"tag": pick[1], "unit": pick[2], **pick[3]}
    # Debt total includes current and noncurrent portions when both are tagged.
    for debt_tag in ("LongTermDebtCurrent", "LongTermDebtNoncurrent"):
        if debt_tag in data:
            rows = [r for unit, rs in data[debt_tag]["units"].items() for r in rs if r.get("end") == latest_end and r.get("form") == "10-K" and r.get("filed", "") <= filing["date"]]
            if rows:
                row = max(rows, key=lambda r: r.get("filed", ""))
                results.setdefault("debt_components", {})[debt_tag] = row.get("val")
    prior_ends = sorted({row.get("end") for tag in TAG_CANDIDATES["total_revenue"] if tag in data for unit, rs in data[tag]["units"].items() for row in rs if row.get("form") == "10-K" and row.get("fp") == "FY" and row.get("end", "") < latest_end})
    results["period_end"] = {"end": latest_end, "prior_end": prior_ends[-1] if prior_ends else None}
    # Capture prior-year values for chosen tags, matching tag and unit.
    for name, fact in list(results.items()):
        if not isinstance(fact, dict) or "tag" not in fact:
            continue
        prior = [row for row in data[fact["tag"]]["units"][fact["unit"]] if row.get("end") == results["period_end"]["prior_end"] and row.get("form") == "10-K"]
        if prior:
            fact["prior_val"] = max(prior, key=lambda r: r.get("filed", "")).get("val")
    return results


def fact_line(label: str, fact: dict) -> str:
    return f"{label}: {fact.get('val')} {fact.get('unit')} | tag={fact.get('tag')} | period={fact.get('start', '')} to {fact.get('end')} | filing={fact.get('accn', '')}"


def print_ratios(facts: dict, price: float | None) -> None:
    def val(key: str) -> float:
        return float(facts[key]["val"])
    revenue, op = val("total_revenue"), val("operating_income")
    net, eps, equity = val("net_income"), val("diluted_eps"), val("equity")
    pri = float(facts["equity"].get("prior_val", 0) or 0)
    avg_equity = (equity + pri) / 2 if pri else equity
    debt_now = sum(facts.get("debt_components", {}).values())
    debt_now = debt_now or float(facts.get("long_term_debt", {}).get("val", 0) or 0)
    cash = val("cash_from_operations")
    capex = abs(val("capex"))
    prior_revenue = float(facts["total_revenue"].get("prior_val", 0) or 0)
    print(f"Revenue growth: ({revenue} - {prior_revenue}) / {prior_revenue} = {(revenue/prior_revenue-1):.4%}" if prior_revenue else "Revenue growth: unavailable (prior-year revenue missing)")
    print(f"Operating margin: {op} / {revenue} = {op/revenue:.4%}")
    print(f"Return on average equity: {net} / (({equity} + {pri}) / 2) = {net/avg_equity:.4%}" if avg_equity else "Return on average equity: unavailable")
    print(f"Debt to equity (current + noncurrent long-term debt): {debt_now} / {equity} = {debt_now/equity:.4%}" if equity else "Debt to equity: unavailable")
    print(f"Free cash flow: {cash} - {capex} = {cash-capex}")
    if price is not None:
        print(f"P/E: price {price} / diluted EPS {eps} = {price/eps:.4f}" if eps else "P/E: unavailable")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Lab 02's EDGAR workflow for a ticker.")
    parser.add_argument("ticker")
    parser.add_argument("--peers", default="", help="Comma-separated peer tickers")
    parser.add_argument("--price", type=float, help="Price per share for P/E")
    parser.add_argument("--step", type=int, choices=range(1, 8), help="Run one step only")
    args = parser.parse_args()
    ua = read_env(BASE / ".env")["SEC_USER_AGENT"]
    ticker = args.ticker.upper()
    stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f_%Z")
    company_out: Path | None = None

    def run_company(symbol: str, primary: bool = False) -> None:
        nonlocal company_out
        print(f"\n=== {symbol} ===")
        step = args.step
        print("STEP 1 — Resolve ticker to SEC CIK")
        cik, company = resolve_ticker(symbol, ua)
        print(f"{symbol} -> CIK {cik} ({company})")
        if step == 1: return
        if step in (4, 5):
            print("\nSTEP 4 — XBRL facts for the latest fiscal year (prior year beside each)")
            kf = recent_filings(cik, ua).get("10-K")
            if not kf:
                raise RuntimeError("No 10-K found")
            facts = get_facts(cik, ua, kf)
            out = BASE / "data" / f"{re.sub(r'[^A-Za-z0-9._-]+','_',company)}_{stamp}"
            out.mkdir(parents=True, exist_ok=True)
            (out / "facts.json").write_text(json.dumps(facts, indent=2), encoding="utf-8")
            for label in ("total_revenue", "operating_income", "net_income", "diluted_eps", "equity", "long_term_debt", "current_debt", "cash_from_operations", "capex"):
                if label in facts:
                    print(fact_line(label, facts[label]) + (f" | prior={facts[label].get('prior_val')}" if "prior_val" in facts[label] else ""))
            if step == 5:
                print("\nSTEP 5 — Calculate ratios from the printed facts")
                print_ratios(facts, args.price)
            print(f"Saved facts to: {out}")
            return
        print("\nSTEP 2 — Select latest 10-K, 10-Q, and Item 2.02 earnings 8-K")
        filings = recent_filings(cik, ua)
        earnings = find_earnings_8k(cik, ua)
        filings["earnings_8k"] = earnings
        for key, filing in filings.items():
            index = filing_index(filing, ua)
            filing["accepted"] = accepted_time(index, filing)
            if filing["accepted"].startswith("Not shown") and filing.get("accepted_datetime"):
                filing["accepted"] = f"{filing['accepted_datetime']} (submissions API fallback; index omitted it)"
            print(f"{key}: {filing['form']} {filing['accession']} | accepted {filing['accepted']} | {filing['primary_document']}")
        if step == 2: return
        out = BASE / "data" / f"{re.sub(r'[^A-Za-z0-9._-]+','_',company)}_{stamp}"
        out.mkdir(parents=True, exist_ok=True)
        if primary: company_out = out
        print(f"\nSTEP 3 — Download and save filing text and metadata: {out}")
        texts: dict[str, str] = {}
        for key in ("10-K", "10-Q"):
            filing = filings.get(key)
            if not filing:
                print(f"Skipped {key}: no filing found")
                continue
            url = f"{SEC}/Archives/edgar/data/{int(cik)}/{filing['accession_nodash']}/{quote(filing['primary_document'])}"
            texts[key] = plain_text(get(url, ua))
            (out / f"{key}_{filing['date']}.txt").write_text(texts[key], encoding="utf-8")
        ef = filings["earnings_8k"]
        texts["release"] = ef["earnings_text"]
        (out / f"8-K_Ex99.1_{ef['date']}.txt").write_text(texts["release"], encoding="utf-8")
        metadata = {k: {kk: vv for kk, vv in f.items() if kk != "earnings_text"} for k, f in filings.items()}
        (out / "filings.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        if step == 3: return
        print("\nSTEP 4 — XBRL facts for the latest fiscal year (prior year beside each)")
        kf = filings.get("10-K")
        if not kf:
            raise RuntimeError("No 10-K found")
        facts = get_facts(cik, ua, kf)
        (out / "facts.json").write_text(json.dumps(facts, indent=2), encoding="utf-8")
        for label in ("total_revenue", "operating_income", "net_income", "diluted_eps", "equity", "long_term_debt", "current_debt", "cash_from_operations", "capex"):
            if label in facts:
                print(fact_line(label, facts[label]) + (f" | prior={facts[label].get('prior_val')}" if "prior_val" in facts[label] else ""))
        if "debt_components" in facts:
            print(f"Long-term debt components (current + noncurrent): {facts['debt_components']}")
        if step == 4: return
        print("\nSTEP 5 — Calculate ratios from the printed facts")
        print_ratios(facts, args.price)
        if step == 5: return
        print("\nSTEP 6 — Earnings release lines: total revenue and diluted EPS")
        release = texts["release"]
        lines = release.splitlines()
        total_row = next((line.strip() for line in lines if re.search(r"\bRevenue was\s+\$", line, re.I)), None)
        if not total_row:
            total_row = next((line.strip() for line in lines if re.match(r"Total (?:net )?revenue|Total net sales\s*\|", line, re.I)), None)
        if not total_row:
            total_row = next((sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", release.replace("\n", " ")) if re.search(r"quarterly revenue|total revenue", sentence, re.I)), None)
        eps_start = next((i for i, line in enumerate(lines) if "NET INCOME PER COMMON SHARE" in line.upper()), None)
        eps_row = None
        if eps_start is not None:
            for line in lines[eps_start + 1:]:
                if "SHARES USED IN CALCULATION" in line.upper():
                    break
                if re.match(r"Diluted\s*\|", line, re.I):
                    eps_row = line.strip()
                    break
        if not eps_row:
            eps_row = next((line.strip() for line in lines if re.search(r"Diluted earnings per share was\s+\$", line, re.I)), None)
        if not eps_row:
            eps_row = next((sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", release.replace("\n", " ")) if re.search(r"diluted (?:earnings per share|EPS)", sentence, re.I)), None)
        print(f"Total revenue row: {total_row}" if total_row else "Total revenue row not found in release")
        print(f"Diluted EPS row: {eps_row}" if eps_row else "Diluted EPS row not found in release")
        if step == 6: return
        print("\nSTEP 7 — Peer facts and operating margin on the same revenue definition")
        for peer in args.peers.split(","):
            peer = peer.strip().upper()
            if not peer: continue
            pcik, pname = resolve_ticker(peer, ua)
            pf = recent_filings(pcik, ua).get("10-K")
            if not pf: print(f"{peer}: no 10-K found"); continue
            p_facts = get_facts(pcik, ua, pf)
            (out / f"{peer}_facts.json").write_text(json.dumps(p_facts, indent=2), encoding="utf-8")
            print(f"{peer} ({pname}) revenue: {p_facts.get('total_revenue', {}).get('val')} | operating income: {p_facts.get('operating_income', {}).get('val')} | margin: {float(p_facts['operating_income']['val'])/float(p_facts['total_revenue']['val']):.4%} | period: {p_facts['period_end']['end']}")

    run_company(ticker, True)
    if company_out and not args.step:
        print(f"\nSaved primary-company filings and facts to: {company_out}")


if __name__ == "__main__":
    main()
