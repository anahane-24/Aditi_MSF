# Lab 05 — page run, gap check, and reflection

**Date:** November 8, 2026  
**Partner's company:** Microsoft (MSFT)  
**Page run:** completed locally with Streamlit AppTest because the browser-control host was unavailable.

## Completed work

- Added Streamlit to `requirements.txt` and added the local page in `desk_ui.py`.
- Ran the page on MSFT with AAPL as a peer. The saved run is `data/MICROSOFT_CORP_20261108_194334_627024_Eastern Standard Time/`.
- Ran the page on COST with WMT, TGT, and BJ as peers and price `$992.13`. The saved run is `data/COSTCO_WHOLESALE_CORP_NEW_20261108_195749_454845_Eastern Standard Time/`.
- Both reports have the required five parts, three Insight lines, and a Verifier table. The COST manager checks pass after a documented postprocessing step. The original role outputs are retained in each node output file.
- The Verifier marked Insight claims unsupported even when source lines are listed. This is a reason for the partner to check claims in the filing by hand. Do not present the Verifier marks as human approval.

## Costco gap-check line

The first paragraph of Costco's release reports net sales growth of 11.2% for the quarter and 10.1% for the fiscal year. It does not state that digitally-enabled comparable sales increased 21% during 2026. The 10-K states this at line 458.

## Reflection notes to discuss

**Insight I would trust least:** I would check the Financial Analyst's Costco Insight first. It compares SG&A expense ratios on two bases: reported net sales and net sales after the gasoline price inflation adjustment. I would open 10-K line 482 and confirm that the 10-basis-point decrease and 1-basis-point increase use those two definitions.

**What a scoring persona adds:** A role description says what the analyst covers. A scoring persona adds explicit criteria, thresholds, evidence sources, and a rule for what changes its view. This makes the role's judgment easier to compare across companies and runs.

**Which member's agent team the team starts from, and what it lacks:** ______________________________

**Personal edits after discussion:** _________________________________________________

## Human and class actions still needed

- Partner hand check: completed for MSFT claims C001 and C027 on November 8, 2026. The partner marked both claims correct; see `Lab05_MSFT_partner_check.md`.
- Student: write the three analyst personas in the student's own words. The course says AI must not write these personas.
- Student: complete the team-name and three-name check with the instructor. This is intentionally left for the in-class exchange.
- Partner/team: run the page on the partner's pick in front of them and confirm that they can read the verified report without opening a terminal. The MSFT run above is saved; the partner should still confirm the page interaction.
