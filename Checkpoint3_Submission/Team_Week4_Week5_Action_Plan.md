# Team Action Plan: Week 4, Week 5, and Checkpoint 3

**Team:** Three Checks — Aditi Nahane, Shachi, and Mrunalini
**Repository:** https://github.com/anahane-24/Aditi_MSF
**Purpose:** Give the team one current checklist, the files to inspect, and an Orca prompt for the partner review.
**Status date:** 2026-11-23

## Start here

The team can start now. Aditi's exchange-price check and reading notes do not block the partner's page run or filing checks. A future live report must wait for a new eligible filing.

Use this file with `Partner_Run_and_Review_Instructions.md`. Some older status documents still say that Aditi's price check and reading notes are pending. Aditi now reports that she personally checked the COST close against Nasdaq and that both showed $896.48 for September 24, 2026. Her reading and EDGAR notes are saved in `week4_reading_and_edgar_examples.md`. The detailed SEC run evidence is in the saved run folders.

## What is already in the project

- The repository has the desk pipeline, CrewAI Flow, seven SEC steps, deterministic worksheet, verifier, evidence hook, close reader, seeker, and Streamlit page.
- The page previously started and returned HTTP 200. A partner still needs to run the page on the partner's selected company and record the result.
- The November 22 GOOGL and MSFT practice runs and their corrected reports are in the repository. Each corrected report has 21/21 model-verifier marks correct, 21 evidence-hook checks passed, and a passing worksheet hook. The raw model outputs and their refusals remain saved. These are practice runs; they do not meet the 24-hour live-report rule.
- The team's valuation rules and investor persona agree on the course owner-cash-flow formula, the three DCF cases, the Margin of Safety rule, and the $10,000,000 portfolio.
- `config/spinoff_factors.md` is the team-written factor list. `config/spinoff_factors.json` has the same window, four factors, directions, thresholds, weights, and source chapters.
- The seeker found 56 Form 10 filings in its saved run. It ranked 0 because four factor values were unavailable: post-distribution selling pressure, relative capitalization size, debt to equity, and insider ownership. The screen must keep candidates unranked when evidence is missing.
- The team's project focus is the filing evidence hook and its audit trail.
- The team has a draft Checkpoint 3 page. Aditi will make the Brightspace submission herself. Do not upload it for her.

## Files the team should inspect

1. `Checkpoint3_Submission/Checkpoint3_Team_Proposal.md` — team, desk design, roles, project focus, and practice-run record.
2. `Checkpoint3_Submission/Lab09_GOOGL_MSFT_Comparison.md` — corrected-run details and the blank partner hand-check rows.
3. `Checkpoint3_Submission/Partner_Run_and_Review_Instructions.md` — partner clone/pull steps, page run, manual claim checks, report copy, and live-report steps.
4. `Checkpoint3_Submission/Week4_Week5_Readiness_Audit.md` — technical and course readiness record. Some personal-work entries are now stale; use this action plan for the latest status.
5. `week4_reading_and_edgar_examples.md` — Aditi's supplied reading responses and the Honeywell and 5C filing details.
6. `config/spinoff_factors.md` and `config/spinoff_factors.json` — hand-written factor choices and the scoring configuration.
7. `screens/latest/20261122_152259/screen.md` — the 56-candidate screen and its data gaps.
8. These saved practice runs:
   - GOOGL: `data/Alphabet_Inc._20261122_175042_244778_Eastern Standard Time/`
   - MSFT: `data/MICROSOFT_CORP_20261122_175421_909473_Eastern Standard Time/`

For each practice run, inspect `verified_report.md`, `report.md`, `verification_marks.json`, `final_hook_marks.json` or `replay_hook_marks.json`, `worksheet_hook_marks.json`, `facts.json`, `filings.json`, and the saved filing text. The corrected report is separate from the raw model report. Do not replace either file.

## Work the team still needs to do

### A. Confirm the partner's Google ticker

The confirmed Google ticker is `GOOGL` (Alphabet Class A). A successful technical page run is recorded in `Mrunalini_GOOGL_Page_Run.md`. The 2 personal SEC filing checks remain pending.

### B. Run the desk from the page on the partner's company

The partner starts the local page and runs the selected ticker from the page. The partner records the run folder and the node names in order. The fixed base order is:

`Steps → Research Analyst → Financial Analyst → Investment Advisor → Strategy Manager → Verifier`

A role may run one more time if the Strategy Manager asks for its one allowed revision. Confirm that the Verifier runs automatically and that its marks appear under the report's first filing line. Confirm that the report has three `Insight:` lines and that each line has a filing source. Save the report and a short record of the page run. Keep any failed run and error output.

### C. Complete the partner's two hand checks

The partner must personally open two report claims in the saved filing text or SEC filing. The partner records each claim, exact line, accession, value, period, mark (`correct` or `wrong`), and corrected value if needed. The model verifier's marks do not count as the partner's marks.

After the partner gives the two marks, the Orca agent can copy those supplied results into a separate `partner_reviewed_report.md` and the comparison sheet. The agent must not choose, invent, or infer the partner's marks. Keep `report.md`, filing text, `facts.json`, model-verifier marks, and evidence-hook marks unchanged.

### D. Finish the seeker work with evidence

Review candidates in `screens/latest/20261122_152259/screen.md`. First check the Form 10 and amendments. Confirm whether each candidate is a true spinoff and find the parent and distribution date. Then look for a source for each factor:

- Return during the declared 90-day period after distribution.
- Spinoff market capitalization divided by parent market capitalization.
- Debt divided by equity, with the filing and period recorded.
- Insider ownership, with the filing section and date recorded.

Use filings or an approved data source. Save a source beside every input and print the points by factor. Do not estimate a missing value. If a factor is not supported, keep that candidate unranked and show the missing field. Rerun the screen after the supported inputs and code changes are ready. Run the existing tests required by the lab and record the command and result. Do not add unrelated tests.

### E. Finish the remaining personal and team prework

- Aditi: record the agent skills and hooks pages she read. Include the local skill path, required first file, how the agent lists a skill, and how a hook can stop an action.
- Aditi: ask the chosen model its cutoff question in a fresh chat with tools off. Record the answer and a provider documentation link. If no cutoff is disclosed, write `not disclosed` and record the documentation page checked.
- Team: choose one upcoming eligible earnings release, a primary runner, and a backup runner. Record the company, ticker, expected release date (or `date not announced`), filing page to watch, names, and decision date.
- Team: the filing evidence hook is the selected project focus. Record any further scope or ownership decision if the team changed it.

### F. Record the next live report

After the selected company files an earnings release, the named runner must run the desk within 24 hours of the filing's EDGAR Accepted time. Use the page if required by the lab. Save the complete run folder, filing time, accession, run time, report, facts, node inputs and outputs, verifier marks, hook marks, and errors. A November 22 practice run is not a live report. If no eligible filing has happened, leave the live report marked pending.

## How to use GitHub with a Pull Request

The course says Issues, Pull Requests, and merges are optional. The team wants a Pull Request so the evidence and changes can be reviewed before they enter `main`.

### Get the current files in Orca

For a new local copy:

```powershell
git clone https://github.com/anahane-24/Aditi_MSF.git
cd Aditi_MSF
python -m pip install -r requirements.txt
```

The main requirements file installs CrewAI and Streamlit. Install
`requirements-lseg.txt` in a separate LSEG-reader environment because its
`httpx` requirement conflicts with CrewAI 1.15. The main desk can instead read
an approved LSEG CSV export from `LSEG_CLOSES_FILE`; keep the export outside
the repository.

For an existing clone:

```powershell
git switch main
git pull origin main
python -m pip install -r requirements.txt
```

Keys are not stored in the repository. Each person must use their own authorized credentials in a local `.env`. Never commit `.env`, API keys, or LSEG secrets.

### Make a branch and Pull Request

After the human partner has completed the checks and the team has reviewed the changes:

1. Create a branch in Orca, for example `partner-review-shachi`:

```powershell
git switch -c partner-review-shachi
```

2. Add only the files that contain the partner's real work. Usually these are the partner-reviewed report, the two rows in `Checkpoint3_Submission/Lab09_GOOGL_MSFT_Comparison.md`, and a small page-run record. Do not stage `.env`, keys, raw filing changes, facts changes, or verifier-mark changes.
3. Review `git status` and `git diff --staged`. Confirm the file list and every mark before committing.
4. Commit and push the branch:

```powershell
git add Checkpoint3_Submission/Lab09_GOOGL_MSFT_Comparison.md
# Add the partner-reviewed report and page-run note by their exact paths.
git commit -m "Add partner review evidence"
git push -u origin partner-review-shachi
```

5. Open the GitHub repository. Select **Compare & pull request**. Set the base to `main` and the compare branch to `partner-review-shachi`. Describe the page run, two manual checks, and any code or data changes. Do not claim a check that the partner did not do.
6. Aditi and the team review **Files changed**. Check that no secret is present and that only intended files changed. Merge only after the team agrees.

If the partner cannot push to this repository, the partner forks the repository, pushes the branch to the fork, and opens a Pull Request from the fork to `anahane-24/Aditi_MSF:main`. Do not put API keys or licensed data in the Pull Request.

## Copy this prompt into the partner's Orca agent

```text
We are the Three Checks team. Help me review our FIN 67110 project in this Orca workspace.

First update the clone from the repository's main branch. Read these files before you change anything:
- Checkpoint3_Submission/Team_Week4_Week5_Action_Plan.md
- Checkpoint3_Submission/Partner_Run_and_Review_Instructions.md
- Checkpoint3_Submission/Checkpoint3_Team_Proposal.md
- Checkpoint3_Submission/Lab09_GOOGL_MSFT_Comparison.md
- Checkpoint3_Submission/Week4_Week5_Readiness_Audit.md
- week4_reading_and_edgar_examples.md

Then inspect the saved GOOGL and MSFT practice-run folders named in the action plan. Explain where each raw report, corrected verified report, filing text, facts file, node input/output, model-verifier marks, and evidence-hook marks are. Explain which report passed the saved checks and which original output was refused. Do not edit a source, report, fact, or mark file during this first review.

Use the confirmed partner ticker, GOOGL. Do not substitute GOOG.

Help me review the saved successful GOOGL page run and its failed predecessors. The successful run is recorded in `Mrunalini_GOOGL_Page_Run.md`. Preserve every failed run and exact error.

For the two required filing checks, show me the report's source and the matching saved filing lines. Do not mark a claim for me. Wait while I personally open each source and choose `correct` or `wrong`. If a claim is wrong, show the cited evidence and let me state the corrected value and period. Record only the marks, lines, initials, and date that I give you. Then create a separate partner_reviewed_report.md and copy the same two rows into the comparison sheet. Do not edit the raw report, filings, facts.json, model-verifier marks, or evidence-hook marks.

For the seeker, inspect the 56-candidate screen and identify which factor inputs are missing. For each possible input, give me the candidate, source filing or approved market-data source, period/window, calculation, and missing evidence. Do not invent or estimate values. Keep a candidate unranked if a value has no source. Show me proposed code changes before you make them. After I approve the supported changes, run the existing lab-required tests and report the exact command and results.

Help the team record a live-release choice: company, ticker, expected date or `date not announced`, EDGAR page to watch, primary runner, backup runner, team members, and decision date. Do not create a live report before the filing. When it files, the named runner must run the desk within 24 hours of the EDGAR Accepted time and save the full evidence folder.

For GitHub, put only approved partner review files and any reviewed code changes on a new branch. Show me `git status` and the staged diff. Never stage `.env`, keys, filings, facts, or verifier marks. Commit and push the branch, then give me the Pull Request URL. Do not merge it. Do not upload anything to Brightspace.
```

## Final checks before the Pull Request

- The partner confirmed the exact ticker.
- The partner used the page and recorded the run folder and node order.
- The Verifier ran, and its table is under the first filing line.
- The report has three sourced `Insight:` lines.
- The partner personally checked 2 claims and supplied both marks.
- The saved raw run and source files remain unchanged.
- The GitHub branch contains only reviewed, intended files and no secrets.
- The Pull Request is open for team review. Merge only after agreement.
- A live report remains pending until a new eligible filing is run within 24 hours.
- Aditi uploads the required Markdown page to Brightspace herself.
