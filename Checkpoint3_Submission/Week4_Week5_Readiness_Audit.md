# Week 4 and Week 5 Readiness Audit

**Checked:** 2026-11-23
**Team:** Three Checks ? Aditi Nahane, Shachi, and Mrunalini
**Scope:** Labs 06?09 and Checkpoint 3 preparation.

## Status summary

| Work | Status | Evidence and open item |
|---|---|---|
| Lab 06 ? The seeker | **Partial** | The seeker, hand-authored factor list, configuration, and five synthetic tests exist. The EDGAR run found 56 Form 10 filings and ranked 0 because factor inputs were unavailable. The two required hand-found EDGAR examples are not recorded. See `screens/latest/20261122_152259/screen.md`. |
| Lab 07 ? Your investor | **Partial** | The team-authored persona and valuation inputs now match the course owner-cash-flow formula, three DCF cases, Margin of Safety rule, and $10,000,000 portfolio. Worksheet source and arithmetic checks pass on GOOGL and MSFT. The hand-written reading responses and future live report remain open. |
| Lab 08 ? One desk | **Partial** | `desk_pipeline.py`, `desk_ui.py`, screen mode, timing output, and offline replay exist. Streamlit is installed and the page returned HTTP 200 at `http://127.0.0.1:8501`. The partner has not run the page and recorded the node order or report. |
| Lab 09 ? Prove it together | **Technical report checks pass on corrected reports; partner checks pending** | Original agent reports remain preserved and failed their hooks. Separate source-corrected reports are saved in the November 22 GOOGL and MSFT runs. Each corrected report has 21 model-verifier marks of `correct`, 21 evidence-hook passes, and a passing worksheet hook. The correction does not erase the raw failure or count as a partner hand-check or partner page run. Partner confirmation of GOOGL vs GOOG is pending. |
| Checkpoint 3 proposal | **Prepared locally; not submitted** | `Checkpoint3_Team_Proposal.md` records the team, members, design, joins, ownership, roles, and live-record status. Brightspace upload remains for Aditi. |
| GitHub issue / pull request / merge | **Optional** | The course says this workflow is optional. |

## November 22 run record

| Ticker | Run folder | EDGAR Accepted time (Eastern) | Raw agent report | Corrected report | Verifier / evidence hook |
|---|---|---|---|---|---|
| GOOGL | `data/Alphabet_Inc._20261122_175042_244778_Eastern Standard Time` | 2026-10-28 16:01:33 | Refused: 6 claims; retained in `report.md` and `final_hook_marks.json` | `verified_report.md` | 21/21 model marks correct; offline evidence replay 21 passed, 0 refused; worksheet hook passed |
| MSFT | `data/MICROSOFT_CORP_20261122_175421_909473_Eastern Standard Time` | 2026-10-28 16:04:44 | Refused: 7 claims; retained in `report.md` and `final_hook_marks.json` | `verified_report.md` | 21/21 model marks correct; offline evidence replay 21 passed, 0 refused; worksheet hook passed |

The original runs reviewed by Shachi are also retained: `data/Alphabet_Inc._20261122_162736_224701_Eastern Standard Time` and `data/MICROSOFT_CORP_20261122_163057_Eastern Standard Time`. A first GOOGL rerun stopped when the Strategy Manager returned malformed JSON; its error is in `data/Alphabet_Inc._20261122_174504_278128_Eastern Standard Time/node_io/strategy_manager_attempt_1_output.json` and its raw response diagnostic is preserved in the same run. The failed complete runs and their hook marks remain saved.

The GOOGL correction separates Q3 net income of $26,170 million from year-to-date net income of $200,855 million. It preserves the original model output and filing text. Neither `facts.json` nor a filing text was edited to obtain a pass. The corrected reports are separate source-backed documents. The model-created `report.md`, `role_outputs.json`, original refusal marks, failed hook marks, and run logs remain available for review.

Both ticker runs occurred on November 22, 2026, after their October 28, 2026 earnings releases. They are practice runs. They do not count as a report recorded within 24 hours of a release.

## Team-authored valuation rules

The persona, valuation specification, policy, and worksheet agree on owner cash flow = net income + depreciation - capital spending; bear, base, and bull rates; Margin of Safety as the deciding number; and a $10,000,000 client portfolio. The worksheet treats discounted owner cash flow as an equity cash-flow proxy and divides by diluted shares. It does not call the result enterprise value or subtract debt again. It uses the explicit Gordon-growth formula and does not use terminal multiples.

## Still required from people

1. Shachi must confirm whether the partner chose `GOOGL` or `GOOG`. Aditi said to use `GOOGL`; partner confirmation is still pending.
2. The partner must open at least two claims in the cited filings and record the partner's own marks and exact lines in `Lab09_GOOGL_MSFT_Comparison.md`. Do not copy AI verifier marks into this table.
3. The partner must run the local page on the partner's company and record that the node order is unchanged and the verified report appears.
4. Aditi must check one close against an exchange source herself if the instructor requires a student demonstration. The saved LSEG close is not Aditi's own hand check.
5. Week 4 prework remains open in `week4_prework_status.md`: read and write the two chapter responses; record one spinoff and one non-spinoff Form 10 example from EDGAR; read the agent skills and hooks pages; and before Session 7 complete the seeker run, cutoff question, live-release choice and team-owned Thursday build.
6. The team must record its first eligible live-release report within 24 hours of a filing. The November 22 GOOGL and MSFT runs are not live reports.
7. Aditi must upload the required Markdown page to Brightspace. No Brightspace submission was made.

## Course references

- [Week 4](https://cinderzhang.github.io/FIN67110-Fall2026/week-04/index.html)
- [Lab 06: The seeker](https://cinderzhang.github.io/FIN67110-Fall2026/week-04/lab-06-investor-skill.html)
- [Lab 07: Your investor](https://cinderzhang.github.io/FIN67110-Fall2026/week-04/lab-07-your-investor.html)
- [Week 5](https://cinderzhang.github.io/FIN67110-Fall2026/week-05/index.html)
- [Lab 08: One desk](https://cinderzhang.github.io/FIN67110-Fall2026/week-05/lab-08-one-desk.html)
- [Lab 09: Prove it together](https://cinderzhang.github.io/FIN67110-Fall2026/week-05/lab-09-prove-it-together.html)
