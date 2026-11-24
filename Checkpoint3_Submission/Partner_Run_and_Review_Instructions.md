# Lab 09 Partner Run and Review Instructions

**For:** Aditi's teammate running Lab 09 in their own Orca workspace
**Repository:** https://github.com/anahane-24/Aditi_MSF
**Run and review evidence:** commit `ecf83b6dc2fc19a6106e1e20a7ed7ad72baa88b2`

## Please start now

You can inspect the existing work and complete your partner checks now. Aditi's reading work and price check do not need to finish first. A future live-release run must wait until the team has a new eligible filing.

The course instructions Aditi shared require the partner to run the team from the page and hand-check 2 claims. They also require the node order to stay fixed and the Verifier table to appear under the filing line. The separate course note says that Issues, Pull Requests, and merges are optional. A Pull Request is a useful way to share your review, but it is not a course requirement by itself.

## What is in the repository now

The original run folders and the November 22 reruns include filing texts, facts, market data, node inputs and outputs, model reports, worksheet records, verifier marks, and evidence-hook marks. The raw model reports that failed remain preserved as `report.md`. Separate corrected reports are saved as `verified_report.md`.

| Ticker | Run folder | Corrected marked report |
|---|---|---|
| GOOGL | `data/Alphabet_Inc._20261122_175042_244778_Eastern Standard Time` | `verified_report.md` |
| MSFT | `data/MICROSOFT_CORP_20261122_175421_909473_Eastern Standard Time` | `verified_report.md` |

Both corrected reports have 21 model-verifier marks of `correct`, 21 offline evidence-hook passes, and a passing worksheet hook. The raw model reports failed their hooks. Read the raw `report.md`, `final_hook_marks.json`, and `role_outputs.json` if you want to see those original failures. Do not replace or delete them.

The GOOGL report separates Q3 net income of $26,170 million from year-to-date net income of $200,855 million. The MSFT report uses the GOOGL peer facts saved in its run folder. The confirmed Google ticker is `GOOGL`.

## Open this project in your Orca workspace

If you do not have the repository in Orca yet, open an Orca terminal and run:

```powershell
git clone https://github.com/anahane-24/Aditi_MSF.git
cd Aditi_MSF
python -m pip install -r requirements.txt
```

If you already cloned it, open that repository in Orca and update it:

```powershell
git pull origin main
python -m pip install -r requirements.txt
```

CrewAI 1.15 and `lseg-data` 2.x require incompatible `httpx` versions. The
main requirements file therefore installs the agent team and page. If you use
the LSEG desktop reader directly, install `requirements-lseg.txt` in a
separate reader environment. The main desk can use an approved LSEG CSV export
through `LSEG_CLOSES_FILE`; keep that export outside the project folder.

The API keys are not in GitHub. If you run the model team, use only credentials that you are authorized to use. Put them in your own local `.env` file. Do not put a key in GitHub, an Issue, or a Pull Request. Do not copy Aditi's `.env` or ask her to publish it. If you do not have an authorized model key or LSEG access, tell Aditi what is missing; do not invent a key or a price.

## Orca prompt 1: inspect the saved work

Paste this into your Orca coding agent before making changes:

> Read `Checkpoint3_Submission/Checkpoint3_Team_Proposal.md`, `Checkpoint3_Submission/Lab09_GOOGL_MSFT_Comparison.md`, and `Checkpoint3_Submission/Week4_Week5_Readiness_Audit.md`. Inspect the two November 22 run folders listed in the comparison file. Summarize, with paths, the raw model report, corrected verified report, filing texts, facts, verifier marks, worksheet marks, and evidence-hook marks for the company I selected. Tell me whether the fixed node order is visible in its saved run. Do not edit any file. Do not change a filing, facts file, report, or verifier mark. Do not call a model or use a hand-check mark as your own. First ask me to confirm whether I selected GOOGL or GOOG for Google.

## Run the page on your selected company

Start the local page from the Orca project terminal:

```powershell
python -m streamlit run desk_ui.py
```

Open the local address printed by Streamlit, normally `http://localhost:8501`. Enter the exact ticker you selected, add peers if you want them, and press Run. Use the page for this partner run. Do not substitute a terminal run for the required page run.

Record the names shown by the page, in order. The base flow order is Steps, Research Analyst, Financial Analyst, Investment Advisor, Strategy Manager, Verifier. A role may appear again if the Manager requests its one allowed revision. Confirm that the Verifier runs and that the final verified report appears with its marks. Save a screenshot of the page result or record the local run folder path.

If the page fails, copy the exact first error line and the run folder path for Aditi. Do not change filing texts or facts to make the page pass.

## Do the 2 independent filing checks by hand

Choose 2 core claims in the report for the company you selected. Check each claim against the saved filing text and, where possible, the SEC filing itself. The model verifier's marks are useful evidence. They are not your hand-check marks.

Examples you can choose after you confirm the ticker:

- For GOOGL: Q3 revenue of $127,577 million, line 56; Q3 net income of $26,170 million, line 39; or diluted EPS of $2.12, line 40. These are in `8-K_Ex99.1_2026-10-28.txt` in the GOOGL run folder. The release identifies the quarter columns at lines 22?25 and year-to-date columns at lines 160?161.
- For MSFT: Q1 revenue of $92.3 billion, line 9; GAAP diluted EPS of $4.92, line 12; or the quarter end at line 8. These are in `8-K_Ex99.1_2026-10-28.txt` in the MSFT run folder.

For each claim:

1. Open the cited filing text yourself.
2. Find the exact line and accession in the filing record.
3. Compare the claim, value, unit, and period with the filing.
4. Write `correct` or `wrong`. If wrong, write the corrected value and period.
5. Record the filing name, line, accession, your initials, and the date you checked it.

The course asks for both marks at the top of the report. Preserve the existing `verified_report.md`. Make a separate copy named `partner_reviewed_report.md` and put your hand-check table directly after the first `Filings read:` line. Keep the Verifier table below it. Also fill the two blank rows in `Checkpoint3_Submission/Lab09_GOOGL_MSFT_Comparison.md`. Do not sign a claim you did not open and check.

Use this table in your copy of the report:

```markdown
## Partner hand check

Partner: [your name]  Date: [YYYY-MM-DD]

| Claim | Filing and accession | Exact line | Partner mark | Corrected value if wrong |
|---|---|---:|---|---|
| [claim 1] | [filing, accession] | [line] | [correct / wrong] | [value or blank] |
| [claim 2] | [filing, accession] | [line] | [correct / wrong] | [value or blank] |
```

## Orca prompt 2: create a review copy only

After you finish both checks by hand, you can give your Orca agent this prompt to add your written results. First tell it your two marks and lines. Do not ask it to choose marks for you.

> Make a copy of the selected company's `verified_report.md` named `partner_reviewed_report.md` in the same run folder. Preserve its first `Filings read:` line and all existing verifier content. Insert this Partner hand check table immediately after the first line, using only the two marks, filing names, accessions, exact lines, initials, and date that I provide. Do not infer or invent a mark, source, value, person, or date. Also copy the same two rows into the blank Partner hand-check record in `Checkpoint3_Submission/Lab09_GOOGL_MSFT_Comparison.md`. Do not edit `report.md`, saved filing texts, `facts.json`, `verification_marks.json`, or evidence-hook marks. Show me the diff before you save it.

## Share your review with the team

The course does not require a Pull Request. If you and Aditi want the changes reviewed before they enter `main`, use a branch and Pull Request. If you cannot push a branch to this repository, make a fork and open a Pull Request from the fork. Do not merge until the team agrees.

Optional Orca prompt for that step:

> Put only my completed `partner_reviewed_report.md` and the two hand-check rows in `Checkpoint3_Submission/Lab09_GOOGL_MSFT_Comparison.md` on a new branch. Do not stage `.env`, API keys, filing edits, facts edits, or verifier-mark edits. Show me the staged file list and diff. Then commit and push the branch and open a Pull Request. Do not merge it.


## Team live-release choice and the future live report

The team can make the choice now. The actual live run must wait until the selected company files an eligible earnings release.

### Record the team's choice

Aditi, Shachi, and Mrunalini should agree on these items and save the decision in the team notes:

1. **Company and ticker:** Choose the company whose next earnings release the team will cover.
2. **Release to watch:** Record the expected date if the company has announced one. If not, write “date not announced” and check the company Investor Relations page or EDGAR later.
3. **Runner:** Name one teammate who will watch for the filing and run the desk.
4. **Backup runner:** Name another teammate in case the runner is unavailable.
5. **Run method:** Use the Streamlit page if Lab 08 or Lab 09 requires the page run. Record where the team will check for the filing.

Use this record:

```text
Company:
Ticker:
Next release date or “date not announced”:
Filing page to watch:
Primary runner:
Backup runner:
Team members who agreed:
Decision date:
```

### Run and save the live report

When the selected company files its earnings release:

1. Open the EDGAR filing index and record the filing date, time, and accession number. Use the EDGAR “Accepted” time as the filing time.
2. The named runner starts the desk within 24 hours of that filing time. Use the local page when the course requires a page run. Do not use an earlier practice run as the live report.
3. Record the page's node order. Confirm that the Verifier runs and that the final report shows its marks.
4. Save the complete run folder. Keep the filing texts, facts, node inputs and outputs, report, verifier marks, evidence-hook marks, and any error log.
5. Add this record to the team's live-report log:

```text
Company and ticker:
EDGAR filing link:
Accession number:
Accepted time and time zone:
Desk run time and time zone:
Runner:
Run folder:
Verifier and evidence-hook result:
```

6. If a check fails, keep the failed output and marks. Fix the source, code, or instructions, then run it again. Do not edit a filing or facts file to force a pass.
7. If no eligible release has been filed, keep the live report marked pending. The team can still complete the company, runner, and backup choices now.
## Still pending after your review

- Aditi reports that she ran the COST close reader and checked Nasdaq herself: both showed $896.48 for 2026-09-24. Add this result to the team record if the course asks for written evidence.
- The remaining Week 4 reading, EDGAR, skills/hooks, and cutoff items listed in `week4_prework_status.md`.
- A future live report within 24 hours of a new filing. The November 22 practice runs do not meet that timing rule.
- Aditi's Brightspace upload. She will submit it herself.
