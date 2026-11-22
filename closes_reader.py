"""Read official daily closes from an LSEG Workspace session or a local CSV export."""

from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import desk_steps


BASE = Path(__file__).resolve().parent
EASTERN = ZoneInfo("America/New_York")
_EXCHANGE_SUFFIXES: dict[str, str] | None = None


@dataclass(frozen=True)
class Close:
    ticker: str
    date: str
    value: float
    source: str
    ric: str | None = None


def parse_filed(value: str | None, accepted: str | None) -> datetime:
    """Parse the override or EDGAR Accepted time as Eastern time."""
    raw = (value or accepted or "").strip()
    if not raw:
        raise ValueError("No filing time is available. Give --filed YYYY-MM-DDTHH:MM:SS.")
    raw = raw.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=EASTERN)
    return parsed.astimezone(EASTERN)


def _export_path(raw: str) -> Path:
    path = Path(os.path.expandvars(raw.strip().strip('"'))).expanduser().resolve()
    if path == BASE or BASE in path.parents:
        raise ValueError("Keep the LSEG close export outside the work folder.")
    return path


def _csv_close(path: Path, ticker: str, filed: datetime) -> Close | None:
    if not path.exists():
        return None
    candidates: list[tuple[date, float]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            symbol = (row.get("ticker") or row.get("symbol") or "").strip().upper()
            day = (row.get("date") or row.get("trade_date") or "").strip()[:10]
            raw_close = row.get("close") or row.get("price_close") or row.get("TR.PriceClose") or ""
            try:
                day_value = date.fromisoformat(day)
                close_value = float(raw_close.replace(",", ""))
            except (ValueError, AttributeError):
                continue
            close_time = datetime.combine(day_value, time(16, 0), EASTERN)
            if symbol == ticker.upper() and close_time <= filed and close_value > 0:
                candidates.append((day_value, close_value))
    if not candidates:
        return None
    day_value, close_value = max(candidates, key=lambda item: item[0])
    return Close(ticker.upper(), day_value.isoformat(), close_value, f"CSV: {path}")


def _exchange_suffix(ticker: str, env: dict[str, str]) -> str | None:
    """Map a SEC ticker to its exchange RIC suffix."""
    global _EXCHANGE_SUFFIXES
    if _EXCHANGE_SUFFIXES is None:
        user_agent = env.get("SEC_USER_AGENT", "").strip()
        if not user_agent:
            return None
        request = Request(
            "https://www.sec.gov/files/company_tickers_exchange.json",
            headers={"User-Agent": user_agent},
        )
        try:
            with urlopen(request, timeout=20) as response:
                payload = json.load(response)
            fields = payload.get("fields", [])
            ticker_column = fields.index("ticker")
            exchange_column = fields.index("exchange")
            suffixes: dict[str, str] = {}
            for row in payload.get("data", []):
                exchange = str(row[exchange_column]).strip().lower()
                if "nasdaq" in exchange:
                    suffix = ".O"
                elif "nyse arca" in exchange:
                    suffix = ".P"
                elif "nyse american" in exchange or "american stock exchange" in exchange:
                    suffix = ".A"
                elif exchange == "nyse":
                    suffix = ".N"
                else:
                    continue
                suffixes.setdefault(str(row[ticker_column]).strip().upper(), suffix)
            _EXCHANGE_SUFFIXES = suffixes
        except Exception:
            return None
    return _EXCHANGE_SUFFIXES.get(ticker.upper())


def _ric_candidates(ticker: str, suffix: str | None) -> tuple[str, ...]:
    ordered = [f"{ticker}{suffix}"] if suffix else []
    ordered.extend((f"{ticker}.O", f"{ticker}.N", ticker))
    return tuple(dict.fromkeys(ordered))


def _lseg_close(ticker: str, filed: datetime, app_key: str, suffix: str | None) -> Close | None:
    import lseg.data as ld

    session = ld.session.desktop.Definition(app_key=app_key).get_session()
    ld.session.set_default(session)
    session.open()
    try:
        start = (filed.date() - timedelta(days=14)).isoformat()
        end = filed.date().isoformat()
        # Use the SEC listing exchange first, then try common U.S. RIC forms.
        for ric in _ric_candidates(ticker, suffix):
            try:
                frame = ld.get_history(
                    universe=[ric], fields=["TR.PriceClose"],
                    start=start, end=end, interval="daily",
                )
            except Exception:
                continue
            if frame is None or frame.empty:
                continue
            series = frame.iloc[:, 0] if getattr(frame.columns, "nlevels", 1) == 1 else frame.iloc[:, 0]
            valid: list[tuple[date, float]] = []
            for idx, raw in series.items():
                try:
                    day = idx.date() if isinstance(idx, datetime) else date.fromisoformat(str(idx)[:10])
                    value = float(raw)
                except (ValueError, TypeError):
                    continue
                if datetime.combine(day, time(16, 0), EASTERN) <= filed and value > 0:
                    valid.append((day, value))
            if valid:
                day, value = max(valid, key=lambda item: item[0])
                return Close(ticker.upper(), day.isoformat(), value, "LSEG Data Library: TR.PriceClose", ric)
        return None
    finally:
        session.close()


def _lseg_history(ticker: str, start: date, end: date, app_key: str, suffix: str | None) -> list[Close]:
    import lseg.data as ld

    session = ld.session.desktop.Definition(app_key=app_key).get_session()
    ld.session.set_default(session)
    session.open()
    try:
        for ric in _ric_candidates(ticker, suffix):
            try:
                frame = ld.get_history(
                    universe=[ric], fields=["TR.PriceClose"],
                    start=start.isoformat(), end=end.isoformat(), interval="daily",
                )
            except Exception:
                continue
            if frame is None or frame.empty:
                continue
            series = frame.iloc[:, 0]
            closes: list[Close] = []
            for idx, raw in series.items():
                try:
                    day = idx.date() if isinstance(idx, datetime) else date.fromisoformat(str(idx)[:10])
                    value = float(raw)
                except (ValueError, TypeError):
                    continue
                if start <= day <= end and value > 0:
                    closes.append(Close(ticker.upper(), day.isoformat(), value,
                                        "LSEG Data Library: TR.PriceClose", ric))
            if closes:
                return sorted(closes, key=lambda item: item.date)
        return []
    finally:
        session.close()


def get_last_close(ticker: str, filed: datetime, env: dict[str, str]) -> Close | None:
    export = env.get("LSEG_CLOSES_FILE", "").strip()
    if export:
        return _csv_close(_export_path(export), ticker, filed)
    app_key = env.get("LSEG_APP_KEY", "").strip()
    if not app_key:
        return None
    suffix = _exchange_suffix(ticker, env)
    try:
        return _lseg_close(ticker.upper(), filed, app_key, suffix)
    except Exception:
        return None


def closes_between(ticker: str, start: str, end: str, env: dict[str, str]) -> list[Close]:
    """Return official daily closes in the inclusive date interval."""
    start_day, end_day = date.fromisoformat(start), date.fromisoformat(end)
    if end_day < start_day:
        raise ValueError("end date must be on or after start date")
    export = env.get("LSEG_CLOSES_FILE", "").strip()
    if export:
        path = _export_path(export)
        if not path.exists():
            return []
        values: list[Close] = []
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                symbol = (row.get("ticker") or row.get("symbol") or "").strip().upper()
                day = (row.get("date") or row.get("trade_date") or "").strip()[:10]
                raw_close = row.get("close") or row.get("price_close") or row.get("TR.PriceClose") or ""
                try:
                    day_value, close_value = date.fromisoformat(day), float(raw_close.replace(",", ""))
                except (ValueError, AttributeError):
                    continue
                if symbol == ticker.upper() and start_day <= day_value <= end_day and close_value > 0:
                    values.append(Close(ticker.upper(), day_value.isoformat(), close_value, f"CSV: {path}"))
        return sorted(values, key=lambda item: item.date)
    app_key = env.get("LSEG_APP_KEY", "").strip()
    if not app_key:
        return []
    suffix = _exchange_suffix(ticker, env)
    try:
        return _lseg_history(ticker.upper(), start_day, end_day, app_key, suffix)
    except Exception:
        return []


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Print the last LSEG daily close before an Eastern filing time.")
    parser.add_argument("ticker")
    parser.add_argument("--filed", required=True, help="Eastern filing time: YYYY-MM-DDTHH:MM:SS")
    args = parser.parse_args()
    env = desk_steps.read_env(BASE / ".env")
    filed = parse_filed(args.filed, None)
    close = get_last_close(args.ticker.upper(), filed, env)
    if close is None:
        print("not available")
    else:
        ric = f" ric={close.ric}" if close.ric else ""
        print(f"{close.ticker} close={close.value:.4f} date={close.date} source={close.source}{ric} filed={filed.isoformat()}")


if __name__ == "__main__":
    main()
