# Checkpoint 1 submission materials

This folder collects the desk, the MSFT fallback report, and the source files used by that report.

## Course checkpoint

The course asks for a permalink to a repository commit that holds the desk and a report on the company selected by your partner. A fallback report counts. This folder is committed and pushed. Submit the commit permalink in Brightspace.

The saved report is for MSFT, the company your partner selected. Its latest earnings release is dated October 28, 2026.

## Contents

- `desk_app.py` and `desk_steps.py`: four-role desk and seven data steps.
- `requirements.txt`: Python package list.
- `prompts/lab_03_prompt.md`: reconstructed Lab 3 prompt.
- `reports/MSFT_fallback_report.md`: five-part fallback report. The Purdue GenAI Studio call returned an error, so this is labeled as fallback.
- `review/MSFT_human_verification.md`: Shachi Kaushik's two MSFT claim checks are recorded. The course requires a hand check; confirm with Shachi that she personally checked both claims against the filings. An earlier version in the branch history was labeled AI-assisted.
- `sources/MSFT/`: filings and facts used for the MSFT report.
- `sources/AAPL/`: Apple 10-K used to check peer figures.
- `.env.example`: placeholders only. It contains no API key.

## Setup and run

Install the listed packages:

```powershell
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env`, then enter your own API key and SEC User-Agent in `.env`. Do not submit `.env` or paste a real key into this folder. `.gitignore` excludes `.env`.

Run the MSFT desk with the saved close and peer:

```powershell
python desk_app.py MSFT --peers AAPL --price 531.01 --price-date 2026-10-28 --price-source "StockAnalysis historical data for Nasdaq:MSFT"
```

The saved report is a fallback. The prior Purdue GenAI Studio role call did not return a report.
