# GOOGL and MSFT Report Correction Audit

**Prepared:** 2026-11-23
**Purpose:** Record the raw-run failures, source corrections, and new verifier and hook results for Shachi's review.

## Result

Both complete November 22 ticker reruns produced run folders with filings, facts, node inputs and outputs, worksheet outputs, raw reports, verifier marks, hook marks, and run logs. The raw model reports failed their first report evidence hooks. Separate corrected reports are saved in each run folder. Each corrected report then received 21 `correct` marks from the model verifier and 21 passed marks from the code evidence hook. Each worksheet hook passed.

The original reports and their failed hook marks remain unchanged. `facts.json`, peer fact files, filings, and saved SEC filing text were not edited to obtain a pass. New verifier marks were produced by running the verifier against each corrected report. Prior raw-model marks and failures remain saved with the original report evidence.

## GOOGL period correction

The original GOOGL report paired Q3 revenue of $127,577 million with $200,855 million net income as if both were quarter results. This was a period error. The Q3 2026 release reports revenue of $127,577 million, net income available to common stockholders of $26,170 million, and diluted EPS of $2.12. It reports $200,855 million separately as year-to-date net income. The saved report cites the 8-K Exhibit 99.1 at lines 56, 39, 40, and 160?161/176, accession 0001652044-26-000080.

The original output is preserved as `report.md` in `data/Alphabet_Inc._20261122_175042_244778_Eastern Standard Time`. The corrected source draft is `corrected_final_report.md`. The marked report to review is `verified_report.md`; its model verifier marks are in `verification_marks.json`; and its offline evidence hook result is `replay_hook_marks.json` (21 passed, 0 refused). The worksheet hook passed.

The correction retains FY2025 10-K facts separately from Q3 release figures. It preserves the original error for audit. The previous model claim that used the prior-year quarter's figures as an annual margin is not carried into the corrected report.

## MSFT report correction

The raw MSFT role report included unsupported quarter and segment figures, including claims that annual figures were quarter results. That report remains in `report.md` in `data/MICROSOFT_CORP_20261122_175421_909473_Eastern Standard Time`. The corrected source draft is `corrected_final_report.md`; the marked report to review is `verified_report.md`. It uses FY2026 10-K facts, Q1 FY2027 release lines 8, 9, and 12, GOOGL peer facts, saved LSEG close data, and the code-printed worksheet.

Its model verifier marks are in `verification_marks.json`; its verified report is in `verified_report.md`; and its offline evidence hook result is `replay_hook_marks.json` (21 passed, 0 refused). The worksheet hook passed. The raw report's initial failed hook marks and the original verifier marks are saved separately.

## Code and test changes

- The verifier prompt now directs quarterly claims to the cited quarter filing lines and period headers. It directs peer rows to the mapped peer-facts file. It does not require XBRL facts for prose claims whose cited filing line supports them.
- The verifier receives period-header context for quarter and year-to-date table claims.
- The ratio checker no longer treats narrative risk statements such as "may decrease operating margins" as a ratio formula. It checks the definition only when the claim states arithmetic.
- The Strategy Manager retries once if its response is invalid JSON. Its original response and format-retry response are saved. It does not exceed 2 model calls.
- Test command: `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; uv run --with pytest --with typing-extensions --with tzdata --with idna python -m pytest -q`
- Result: **25 passed**.

The first GOOGL rerun stopped at `strategy_manager_node` with `JSONDecodeError: Unterminated string starting at: line 34 column 22 (char 789)`. The exact error is in `node_io/strategy_manager_attempt_1_output.json`; the response diagnostic is `manager_diagnostic_raw.txt`. The subsequent full GOOGL and MSFT runs completed the agent team but their raw model reports failed hooks. Their `final_hook_marks.json` and full pipeline logs retain the refused claims. The corrected report verification and offline replay passed after the report and verifier evidence were corrected.

## Original runs for partner review

Shachi's original run folders are retained: `data/Alphabet_Inc._20261122_162736_224701_Eastern Standard Time` and `data/MICROSOFT_CORP_20261122_163057_315429_Eastern Standard Time`. The later complete reruns are in the folders listed above. Each folder contains the filing texts, fact files, raw node I/O, reports, marks, and run metadata.

## Still pending

1. The selected Google ticker is confirmed as `GOOGL`.
2. Shachi must independently open and check 2 filing claims and record marks and line references in `Lab09_GOOGL_MSFT_Comparison.md`.
3. The successful technical GOOGL page run is recorded in `Mrunalini_GOOGL_Page_Run.md`.
4. Aditi must perform her own required exchange-close check.
5. The remaining Week 4 work is listed in `week4_prework_status.md`.
6. A future live report must be recorded within 24 hours of an earnings filing. The November 22 practice runs do not satisfy this timing rule.
7. Aditi must upload the Checkpoint 3 Markdown page to Brightspace. No Brightspace upload was made.
