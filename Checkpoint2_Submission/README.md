# Checkpoint 2 — The Verifier

This folder contains the seeded diluted-EPS error test and the Verifier's saved marks. The agent-team code is in the repository root: `agent_team.py`, `desk_app.py`, `desk_steps.py`, `roles/`, and `requirements.txt`.

## Reproduce the test

From the repository root, install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Set `API_KEY`, `MODEL`, and `SEC_USER_AGENT` in the ignored root `.env` file. Then run the Verifier on this saved test folder:

```powershell
python agent_team.py --verify-only "Checkpoint2_Submission\seeded_error_test"
```

The seeded report states diluted EPS as `$21.76`. The saved facts and 10-K report `$20.76` per share for the fiscal year ended `2026-08-30`. The Verifier marks the seeded value `wrong` and gives the actual 10-K source, line `652`, and the corrected amount. The 10-K accession is `0000909832-26-000093`.

See `seeded_error_test/verified_report.md` for the full marks table and `seeded_error_test/verification_marks.json` for machine-readable marks. The filing text is included so a reader can inspect line `652`.

The partner hand-check sheet is `partner_hand_check.md`. `shanashank` confirmed both checks by hand on November 8, 2026. The sheet records the partner marks and cites the exact report and filing lines in this submission.
