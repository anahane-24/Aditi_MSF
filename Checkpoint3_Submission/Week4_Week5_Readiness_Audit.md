# Week 4 and Week 5 Readiness Audit

**Checked:** 2026-11-22  
**Team:** Three Checks — Aditi Nahane, Shachi, and Mrunalini  
**Scope:** Session 6 (Nov 10) through Session 9 (Nov 19), and Checkpoint 3 preparation.

## Status summary

| Work | Status | Evidence and open item |
|---|---|---|
| Lab 06 — The seeker | **Partial** | `spinoff_seeker.py`, the hand-authored factor list, its JSON configuration, and 5 synthetic tests exist. The EDGAR run found 56 Form 10 filings, but ranked 0 because price, distribution, capitalization, debt/equity, and insider data are missing. See `screens/latest/20261122_152259/screen.md`. The partner's hand-found spinoff and non-spinoff examples are not recorded. |
| Lab 07 — Your investor | **Partial** | The team-authored persona and valuation specification now match the course owner-cash-flow formula, the three DCF cases, Margin of Safety, and a $10,000,000 client portfolio. Worksheet arithmetic/source checks pass for GOOGL and MSFT. No eligible live report is saved. |
| Lab 08 — One desk | **Partial** | `desk_pipeline.py`, `desk_ui.py`, screen mode, elapsed-time output, and offline replay are implemented. Streamlit 1.67.0 is installed. Twenty-five unit tests passed. The page returned HTTP 200 at `http://127.0.0.1:8501`; it is running locally. The partner has not run it. Offline replay ran on both saved reports and correctly refused both. No successful final-report replay exists because both model reports failed the evidence hook. |
| Lab 09 — Prove it together | **Partial** | The partner selected Google and Microsoft. Runs exist for GOOGL and MSFT. Both dates are within 30 days of the run date, and both companies are on the course build-out list. The Google ticker uses GOOGL for Alphabet Inc. Class A; confirm this with the partner. Both model reports were refused because they contain unsupported claims or wrong company figures. The updated worksheets and worksheet hooks pass. The 11-claim comparison and blank partner hand-check rows are in `Lab09_GOOGL_MSFT_Comparison.md`. The partner must add at least 2 manual checks. |
| Checkpoint 3 proposal | **Prepared locally; not submitted** | `Checkpoint3_Team_Proposal.md` includes team name, names, diagram, joins, owned work, roles, and the live-record status. There is no eligible live report in `runs/live`. Brightspace upload remains for Aditi. |
| GitHub issue / pull request / merge | **Optional** | The course says the GitHub workflow is optional. No issue or pull request is required for these labs. |

## Lab 09 run record

| Ticker | EDGAR Accepted time (Eastern) | Run time | Report hook | Worksheet hook |
|---|---|---|---|---|
| GOOGL | 2026-10-28 16:01:33 | 2026-11-22 16:27:39 | Refused: 7 claims | Passed |
| MSFT | 2026-10-28 16:04:44 | 2026-11-22 16:31:02 | Refused: 6 claims | Passed |

The latest reports use the updated primary-versus-peer instructions. They are not verified reports. GOOGL copied MSFT's operating figures into its peer analysis; MSFT reported unsupported quarterly facts. Do not submit them as successful Lab 09 runs. Their filed dates were over 24 hours before the run. They cannot fill the live-report requirement.

## Team-authored valuation rules

The updated hand-written persona and valuation specification agree on the course formula, all three case rates, Margin of Safety as the deciding number, and a $10,000,000 client portfolio. The worksheet treats the discounted owner-cash-flow result as an equity cash-flow proxy and divides it by diluted shares. It does not label the result enterprise value or subtract debt again. The policy uses the explicit Gordon-growth formula; the specification no longer lists terminal multiples. Worksheet arithmetic/source checks pass. The model reports remain refused and are not verified.

## Required next actions

1. Aditi must check one price against an exchange source herself if the instructor requires a student demonstration. The local status file records that this hand-check is pending.
2. Complete the two EDGAR examples and the written reading responses if they are still pending in `week4_prework_status.md`.
3. Confirm with the partner that `GOOGL` is the chosen Google ticker. The partner must open filing lines and mark at least 2 claims in `Lab09_GOOGL_MSFT_Comparison.md`.
4. Correct or regenerate both agent reports. The current reports assign Microsoft values to Alphabet and include unsupported claims. The verifier must mark the corrected report, and the evidence hook must pass.
5. Have the partner run the local page. Confirm the page shows node names and a final verified report with marks.
6. Add an eligible live report only when the run and commit meet the course timing rule. Do not relabel the Nov 22 practice runs as live.
7. Commit and push the files needed for the team repository. The working tree contains many older untracked artifacts, so stage only the reviewed Week 4/5 and Checkpoint 3 files. Upload the Checkpoint 3 page to Brightspace separately.

## Course references

- [Week 4](https://cinderzhang.github.io/FIN67110-Fall2026/week-04/index.html)
- [Lab 06: The seeker](https://cinderzhang.github.io/FIN67110-Fall2026/week-04/lab-06-investor-skill.html)
- [Lab 07: Your investor](https://cinderzhang.github.io/FIN67110-Fall2026/week-04/lab-07-your-investor.html)
- [Week 5](https://cinderzhang.github.io/FIN67110-Fall2026/week-05/index.html)
- [Lab 08: One desk](https://cinderzhang.github.io/FIN67110-Fall2026/week-05/lab-08-one-desk.html)
- [Lab 09: Prove it together](https://cinderzhang.github.io/FIN67110-Fall2026/week-05/lab-09-prove-it-together.html)
