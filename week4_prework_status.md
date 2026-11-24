# Week 4 prework status — 2026-11-10

## Done in the project folder

- Installed `lseg-data` version 2.1.1.
- Added `closes_reader.py`. It has functions for daily closes between two dates and the last close before a filing time.
- The reader now checks the SEC ticker/exchange file and uses the matching LSEG RIC suffix first. This avoids selecting a same-ticker security on the wrong exchange.
- Updated the CrewAI desk to read `LSEG_APP_KEY` or `LSEG_CLOSES_FILE` from `.env`.
- The desk reads the earnings 8-K's Accepted time from the saved EDGAR index data. `--filed YYYY-MM-DDTHH:MM:SS` overrides that time. Times use Eastern time.
- The desk saves the close and filing time with each run. The Financial Analyst receives the price, date, and source. If a close is unavailable, the run continues without a market price.
- Updated the local Streamlit page to use the filing-time override instead of a manually supplied price.
- Created the minimal `spinoff-screen` skill file. Its `SKILL.md` contains only the skill name and description.
- Offline checks passed for the close selection before 4:00 PM and at 4:00 PM Eastern. Python syntax checks passed.
- Configured the App Key in the active Orca project `.env` (do not copy the key into Git or chat).
- Live close check: COST on 2026-09-24 returned $896.48 for a 2026-09-24 16:17:37 Eastern filing time. Nasdaq's historical data also shows $896.48. An initial lookup selected `COST.N` and returned $896.64; the SEC exchange lookup corrected it to Nasdaq RIC `COST.O`.

## Still needs your setup or your own work

- Keep LSEG Workspace open and signed in when you run the reader. The active Orca project `.env` now has the App Key. Do not copy the secret to Git or chat.
- The assistant ran one reader check at your request. The course says you run the reader and check a close yourself, so run the command once in your own PowerShell and confirm the match if your instructor expects you to demonstrate it.
- Read Greenblatt, Chapter 3, and write your one-line answer by hand.
- Read Klarman, the spinoff pages in Chapter 10, or use the course's Greenblatt fallback if the library loan is not available. Write your one-line answer by hand.
- Find one recent spinoff filer and one Form 10 filer that is not a spinoff on EDGAR. Record the filing evidence by hand.
- Write your factor list by hand: factor, predicted direction, source chapter, and screen window. The course says AI must not write this list.
- Read the skills and hooks pages for the agents you use. Confirm where your agent stores skills and how it lists the new skill.
- Before Session 7: complete the seeker run and its tests; write the worksheet method, rates, client purchase size, and conviction rule; write the persona in your own six parts; choose the live release and team runner; record the model cutoff answer and its documented cutoff (or “not disclosed” with the page checked); choose as a team what you will own on Thursday.

## Commands

Install or update the package:

```powershell
python -m pip install -r requirements.txt
```

Run the reader yourself after LSEG Workspace and `.env` are ready:

```powershell
python closes_reader.py COST --filed YYYY-MM-DDTHH:MM:SS
```

Run the team. Leave out `--filed` to use the EDGAR Accepted time:

```powershell
python agent_team.py COST --peers WMT,TGT,BJ
```

Use the local page:

```powershell
python -m streamlit run desk_ui.py
```

## Update — 2026-11-22

The team confirmed that `config/spinoff_factors.md`, `config/valuation_worksheet_inputs.md`, and `roles/investor_persona.md` were written by hand. The code uses the factor values in `config/spinoff_factors.json`, which must match the hand-written Markdown file.

The seeker ran from 2025-11-22 through 2026-11-22. It found 56 Form 10 filings. It ranked 0 candidates because all 4 factor inputs were unavailable. The screen is saved at `screens/latest/20261122_152259/screen.md`.

The worksheet and deterministic check ran on the partner's GOOGL and MSFT picks. Both worksheet checks passed. The model reports failed the report evidence hook. See `Checkpoint3_Submission/Lab09_GOOGL_MSFT_Comparison.md`.

The team has now reconciled the persona, valuation specification, policy, and worksheet on the course owner-cash-flow formula, 3-case DCF rates, Margin of Safety, and a $10,000,000 client portfolio. The valuation engine's Sell/Avoid precedence is corrected. All 25 tests pass. Updated GOOGL and MSFT worksheet calculations pass their source/arithmetic hooks and show Sell / Avoid with $0.00 allocation. The raw GOOGL and MSFT model reports failed their evidence hooks and remain preserved. Separate corrected reports in the November 22 run folders each have 21/21 model-verifier marks correct, 21/21 offline evidence-hook passes, and a passing worksheet hook. The raw output remains available for comparison.

Still open: your own exchange-price check; the two hand-found EDGAR examples; the required reading response lines; reading the skills and hooks pages; the remaining pre-Session-7 choices and cutoff record; the partner's two manual filing checks; and a future live report within 24 hours of filing. `GOOGL` is confirmed, and the successful technical page run is recorded in `Checkpoint3_Submission/Mrunalini_GOOGL_Page_Run.md`.


The partner hand checks, Aditi's own price check, and future live report are not completed by the corrected practice reports or the later technical page run. See `Checkpoint3_Submission/Week4_Week5_Readiness_Audit.md` and `Checkpoint3_Submission/Lab09_GOOGL_MSFT_Comparison.md` for run paths and marks.
