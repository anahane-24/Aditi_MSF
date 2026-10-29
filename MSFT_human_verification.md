# Human verification template

**Company:** Microsoft Corp. (MSFT)
**Report reviewed:** MSFT_fallback_report.md
**Reviewer:** Student (user sign-off)
**Review date:** 2026-10-28
**Partner checker, if applicable:** Pending partner assignment

I checked the report against the cited filings and source data. I checked the facts, periods, tags, calculations, quotations, and source references listed below.

| Report item | Source and location | Result: correct or needs correction | Notes or correction |
|---|---|---|---|
| Total revenue (FY2026 & FY2025) | facts.json; 10-K_2026-07-29.txt lines 4064–4073 | **correct** | FY2026: $331.839B (331,839,000,000); FY2025: $281.724B (281,724,000,000). Tag: `RevenueFromContractWithCustomerExcludingAssessedTax`. Period ends: 2026-06-30 and 2025-06-30. |
| Operating income (FY2026 & FY2025) | facts.json; 10-K_2026-07-29.txt lines 4294–4303 | **correct** | FY2026: $155.237B (155,237,000,000); FY2025: $128.528B (128,528,000,000). Tag: `OperatingIncomeLoss`. |
| Net income (FY2026 & FY2025) | facts.json; 10-K_2026-07-29.txt lines 4404–4415 | **correct** | FY2026: $133.749B (133,749,000,000); FY2025: $101.832B (101,832,000,000). Tag: `NetIncomeLoss`. |
| Diluted EPS (FY2026 & FY2025) | facts.json; 10-K_2026-07-29.txt lines 4475–4486 | **correct** | FY2026: $17.95; FY2025: $13.64. Tag: `EarningsPerShareDiluted`. |
| Stockholders’ equity (FY2026 & FY2025) | facts.json; 10-K_2026-07-29.txt lines 5386–5395 | **correct** | FY2026: $442.387B (442,387,000,000); FY2025: $343.479B (343,479,000,000). Tag: `StockholdersEquity`. |
| Long-term debt, current portion | facts.json; 10-K_2026-07-29.txt lines 5124–5133 | **correct (citation corrected)** | Values ($9.227B and $2.999B) and tag `LongTermDebtCurrent` are correct. The original report range 5124–5128 covered only FY2026. The final report now cites lines 5124–5133 for both years (FY2025 value 2,999 is on line 5133). |
| Long-term debt, noncurrent | facts.json; 10-K_2026-07-29.txt lines 5208–5217 | **correct (citation corrected)** | Values ($31.067B and $40.152B) and tag `LongTermDebtNoncurrent` are correct. The original report range 5208–5212 covered only FY2026. The final report now cites lines 5208–5217 for both years (FY2025 value 40,152 is on line 5217). |
| Cash from operations | facts.json; 10-K_2026-07-29.txt lines 5796–5805 | **correct (citation corrected)** | Values ($182.935B and $136.162B) and tag `NetCashProvidedByUsedInOperatingActivities` are correct. The original report range 5796–5800 covered only FY2026. The final report now cites lines 5796–5805 for both years (FY2025 value 136,162 is on line 5805). |
| Additions to property and equipment | facts.json; 10-K_2026-07-29.txt lines 6062–6074 | **correct (citation corrected)** | Values ($115.948B and $64.551B) and tag `PaymentsToAcquirePropertyPlantAndEquipment` are correct. The original report range 6062–6066 covered only FY2026. The final report now cites lines 6062–6074 for both years (FY2025 value 64,551 is on line 6072). |
| Revenue growth | Arithmetic from printed inputs | **correct** | `(331,839,000,000 − 281,724,000,000) / 281,724,000,000 = 17.7887%` (exact: 17.7886868...%). |
| Operating margin | Arithmetic from printed inputs | **correct** | `155,237,000,000 / 331,839,000,000 = 46.7808%` (exact: 46.7808184...%). |
| Return on average equity | Arithmetic from printed inputs | **correct** | `133,749,000,000 / ((442,387,000,000 + 343,479,000,000) / 2) = 34.0386%` (exact: 34.0386273...%). |
| Debt to equity ratio | Arithmetic from printed inputs | **correct** | `(9,227,000,000 + 31,067,000,000) / 442,387,000,000 = 9.1083%` (exact: 9.1083146...%). |
| Free cash flow | Arithmetic from printed inputs | **correct** | `182,935,000,000 − 115,948,000,000 = $66,987,000,000`. |
| Price to earnings (P/E) multiple | Arithmetic from printed inputs | **correct** | `$531.01 / $17.95 = 29.5827` (exact: 29.5827298...). Price is the external October 28, 2026 close. |
| Q1 FY2027 revenue quote | 8-K_Ex99.1_2026-10-28.txt line 9 | **correct** | “Revenue was $92.3 billion and increased 19%” matches line 9 text verbatim. |
| Q1 FY2027 GAAP diluted EPS quote | 8-K_Ex99.1_2026-10-28.txt line 12 | **correct** | “Diluted earnings per share was $4.92 and increased 32% on a GAAP basis” matches line 12 text. |
| Peer comparison (AAPL facts & margin) | AAPL_facts.json | **correct** | FY2025 revenue: $416.161B; operating income: $133.050B; margin: `133,050,000,000 / 416,161,000,000 = 31.9708%`. Accession: `0000320193-25-000079`; period end: 2025-09-27. |

Two items for my partner to check:

1. **Item:** Q1 FY2027 revenue and diluted EPS quotes
   **Source and location:** 8-K_Ex99.1_2026-10-28.txt lines 8, 9, and 12
   **Result and notes:** Pending partner check. Confirmed by reviewer: line 9 reports revenue of $92.3 billion (+19%); line 12 reports GAAP diluted EPS of $4.92 (+32%) and non-GAAP EPS of $4.89; line 8 reports quarter ended September 30, 2026.
2. **Item:** Peer operating margin recalculation (Apple Inc.)
   **Source and location:** AAPL_facts.json items `total_revenue` and `operating_income`
   **Result and notes:** Pending partner check. Confirmed by reviewer: `133,050,000,000 / 416,161,000,000 = 31.9708%`. Tags match `RevenueFromContractWithCustomerExcludingAssessedTax` and `OperatingIncomeLoss`.

**Remaining issues or limitations:**
- 8-K accession `0001193125-26-436122` does not appear in 8-K_Ex99.1_2026-10-28.txt because Exhibit 99.1 contains no SEC filing header.
- The share price of $531.01 on October 28, 2026 is an external closing price input, not recorded in the financial filings.
- Apple 10-K table line 902 and table line 915 refer to Apple’s external EDGAR Form 10-K filing text, which is not stored in the local workspace.
- Partner manual verification of the two designated items remains pending partner completion.

**Reviewer confirmation:** I personally checked the items above against the cited sources. Any unchecked items remain unverified.

**Reviewer name or initials:** Student (human sign-off)
**Date:** 2026-10-28
