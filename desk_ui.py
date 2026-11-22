"""Local browser interface for the fixed SEC equity research agent team."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import streamlit as st


BASE = Path(__file__).resolve().parent
TICKER_RE = re.compile(r"^[A-Za-z0-9.-]{1,12}$")


def parse_tickers(value: str, field: str) -> list[str]:
    tickers = [part.strip().upper() for part in value.split(",") if part.strip()]
    invalid = [ticker for ticker in tickers if not TICKER_RE.fullmatch(ticker)]
    if invalid:
        raise ValueError(f"{field} contains an invalid ticker: {', '.join(invalid)}")
    if len(set(tickers)) != len(tickers):
        raise ValueError(f"{field} contains a duplicate ticker.")
    return tickers


def run_team(ticker: str, peers: list[str], filed: str | None, start_date: str | None) -> tuple[int, str]:
    command = [sys.executable, str(BASE / "desk_pipeline.py"), ticker]
    if peers:
        command.extend(["--peers", ",".join(peers)])
    if filed:
        command.extend(["--filed", filed])
    if start_date:
        command.extend(["--start", start_date])

    process = subprocess.Popen(
        command,
        cwd=BASE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    output: list[str] = []
    activity = st.empty()
    log_view = st.empty()
    with st.status("Agent team is running…", expanded=True) as status:
        assert process.stdout is not None
        for line in process.stdout:
            output.append(line)
            stripped = line.strip()
            if stripped.startswith(("NODE:", "ROLE:", "PART:", "PICK:")) or stripped.startswith("STEP "):
                activity.markdown(f"**Current activity:** `{stripped}`")
            log_view.code("".join(output)[-16000:], language="text")
        return_code = process.wait()
        if return_code == 0:
            status.update(label="Agent team finished.", state="complete", expanded=False)
        else:
            status.update(label="Agent team stopped with an error.", state="error", expanded=True)
    return return_code, "".join(output)


def report_path_from_output(output: str) -> Path | None:
    matches = re.findall(r"Saved verified report:\s*(.+)", output)
    if not matches:
        return None
    report_path = Path(matches[-1].strip()).resolve()
    try:
        report_path.relative_to((BASE / "data").resolve())
    except ValueError:
        return None
    return report_path if report_path.is_file() else None


st.set_page_config(page_title="SEC Equity Research Desk", page_icon="📊", layout="wide")
st.title("SEC Equity Research Desk")
st.write(
    "Enter a company ticker or 'screen' and optional peer tickers. The desk reads the last close before the filing time. "
    "It runs the agent team, worksheet, and evidence hook in a fixed order."
)

with st.form("run_desk"):
    ticker_input = st.text_input("Company ticker or screen", value="MSFT", help="Enter a ticker, or 'screen' to use the spinoff screen")
    peers_input = st.text_input("Peer tickers (optional)", help="Comma-separated, for example AAPL,GOOGL")
    start_date = st.text_input(
        "Screen start date (required only for screen)",
        placeholder="YYYY-MM-DD",
    ).strip()
    filed = st.text_input(
        "Filing time override (Eastern, optional)",
        placeholder="YYYY-MM-DDTHH:MM:SS",
        help="Leave blank to use the Accepted time from the earnings 8-K index page.",
    ).strip()
    submitted = st.form_submit_button("Run agent team", type="primary")

if submitted:
    try:
        tickers = parse_tickers(ticker_input, "Company ticker")
        if len(tickers) != 1:
            raise ValueError("Enter one company ticker.")
        ticker = tickers[0]
        peers = parse_tickers(peers_input, "Peer tickers")
        if ticker in peers:
            raise ValueError("Do not list the company ticker as one of its peers.")
    except ValueError as exc:
        st.error(str(exc))
    else:
        if ticker.lower() == "screen" and not start_date:
            st.error("Enter a screen start date in YYYY-MM-DD format.")
            st.stop()
        return_code, output = run_team(ticker, peers, filed or None, start_date or None)
        if return_code:
            st.error("The agent team did not finish. Review the run log below.")
            st.code(output[-16000:], language="text")
        else:
            report_path = report_path_from_output(output)
            if report_path is None:
                st.warning("The run ended, but the verified report path was not found in the output.")
                st.code(output[-16000:], language="text")
            else:
                st.success(f"Verified report saved to: {report_path}")
                st.subheader("Verified report")
                report = report_path.read_text(encoding="utf-8")
                st.markdown(report)
                st.download_button(
                    "Download verified report",
                    data=report,
                    file_name=report_path.name,
                    mime="text/markdown",
                )
                with st.expander("Run log"):
                    st.code(output[-16000:], language="text")

st.caption("The page uses the API settings in the project .env file. Keep that file private.")
