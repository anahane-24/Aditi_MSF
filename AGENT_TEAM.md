# Fixed Agent Team for the SEC Equity Desk

This desk uses a CrewAI Flow. Code runs the same sequence on each full run:

1. Seven SEC data steps
2. Research Analyst
3. Financial Analyst
4. Investment Advisor
5. Strategy Manager
6. Verifier

The four role instructions are in `roles/`. Each model request uses one JSON payload with `task`, `context`, and `expected_output`. The Manager can request one revision per role. The code controls that route and prevents a role from running more than twice. The Verifier always runs after the Manager on a full run. `--verify-only` runs only the Verifier on an existing run folder.

## Setup

From the workspace root, install the packages:

```powershell
python -m pip install -r requirements.txt
```

Set `API_KEY`, `MODEL`, and `SEC_USER_AGENT` in the root `.env` file. Keep `.env` private.

## Run the team

Replace the ticker, peers, and price with the values for your run:

```powershell
python agent_team.py TICKER --peers PEER1,PEER2 --price 123.45
```

Omit `--peers` or `--price` when you do not need those inputs. The program prints the new run folder.

## Verify a saved run

Use the exact run folder printed at the end of the full run:

```powershell
python agent_team.py --verify-only "data\COMPANY_RUN_FOLDER"
```

The verified report is saved as `verified_report.md` in that folder. Its first line remains the filing list, followed by the verifier table.
