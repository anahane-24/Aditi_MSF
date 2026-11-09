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


def run_team(ticker: str, peers: list[str], price: float | None) -> tuple[int, str]:
    command = [sys.executable, str(BASE / "agent_team.py"), ticker]
    if peers:
        command.extend(["--peers", ",".join(peers)])
    if price is not None:
        command.extend(["--price", str(price)])

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
            if stripped.startswith(("NODE:", "ROLE:")) or stripped.startswith("STEP "):
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
    "Enter a company ticker, optional peer tickers, and an optional share price. "
    "The page runs the fixed agent team and displays its verified report."
)

with st.form("run_desk"):
    ticker_input = st.text_input("Company ticker", value="MSFT", help="Example: MSFT")
    peers_input = st.text_input("Peer tickers (optional)", help="Comma-separated, for example AAPL,GOOGL")
    include_price = st.checkbox("Include a share price for P/E")
    price = st.number_input(
        "Share price (USD)", min_value=0.01, value=500.0, step=0.01,
        help="This value is used only when you select the share-price checkbox.",
    )
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
        return_code, output = run_team(ticker, peers, float(price) if include_price else None)
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
