# Mrunalini GOOGL page-run record

Date: 2026-11-24

Ticker selected for this test: `GOOGL` (Alphabet Inc., Class A).

This was an automated Streamlit page test because the local browser bridge was
not available. It does not replace Shachi's required personal page run or the
partner's 2 independent filing checks.

## Result

- The Streamlit page opened and accepted `GOOGL` in the company-ticker field.
- The Run agent team button started `desk_pipeline.py GOOGL`.
- The pipeline stopped before the first node.
- First error: `ModuleNotFoundError: No module named 'openai'`.
- No run folder and no report were created.
- The report is not verified.

## Successful rerun after the reviewed fixes

- Run time: 2026-11-24 at approximately 15:17 Eastern.
- Interface: Streamlit's page-testing interface entered `GOOGL`, entered
  `MSFT` as the peer, and pressed the page's **Run agent team** button.
- Run folder: `data/Alphabet_Inc._20261124_151701_064742_EST`.
- The page returned no exception and no error message.
- The page displayed: `Verified report saved to: .../desk_final_report.md`.
- Final evidence hook: 14 claims passed; 0 refused.
- Model-verifier table after deterministic exact-fact reconciliation: 14 of
  14 rows marked correct. Raw model responses remain in `node_io`.
- Worksheet hook: passed.
- The original model report, each failed intermediate mark, and the
  source-backed correction remain visible in the run folder.

This is a successful technical GOOGL page run. It does not replace the
partner's 2 personal SEC filing checks. Those checks remain pending.

## Environment findings

- The review clone had no `.env` and no existing `.venv`.
- Installing all packages from `requirements.txt` failed because CrewAI 1.15
  requires `httpx~=0.28.1`, while `lseg-data` 2.x requires `httpx<0.28`.
- Streamlit 1.67.0 was installed alone in the ignored local `.venv` to exercise
  the page without changing the repository's dependency declarations.

The dependency setup is now split: install the core desk from
`requirements.txt`; install the optional LSEG reader in a separate environment
from `requirements-lseg.txt`. This avoids the incompatible `httpx` requirements
of CrewAI 1.15 and `lseg-data` 2.x.
