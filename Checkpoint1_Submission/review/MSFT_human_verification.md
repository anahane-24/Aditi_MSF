# Human verification

**Company:** Microsoft Corp. (MSFT)
**Report reviewed:** MSFT_fallback_report.md
**Reviewer:** Aditi Nahane
**Review date:** 2026-10-28
**Partner checker:** Shachi Kaushik
**Partner check date:** 2026-11-02

The student review below is preserved from the original file. The two designated partner checks were completed by Shachi Kaushik. The partner entries identify the sources, findings, and calculations. 

| Report item | Source and location | Result | Notes or correction |
|---|---|---|---|
| Total revenue (FY2026 & FY2025) | facts.json; 10-K_2026-07-29.txt lines 4064–4073 | correct | FY2026: $331.839B; FY2025: $281.724B. Tag: RevenueFromContractWithCustomerExcludingAssessedTax. Period ends: 2026-06-30 and 2025-06-30. |
| Operating income (FY2026 & FY2025) | facts.json; 10-K_2026-07-29.txt lines 4294–4303 | correct | FY2026: $155.237B; FY2025: $128.528B. Tag: OperatingIncomeLoss. |
| Net income (FY2026 & FY2025) | facts.json; 10-K_2026-07-29.txt lines 4404–4415 | correct | FY2026: $133.749B; FY2025: $101.832B. Tag: NetIncomeLoss. |
| Diluted EPS (FY2026 & FY2025) | facts.json; 10-K_2026-07-29.txt lines 4475–4486 | correct | FY2026: $17.95; FY2025: $13.64. Tag: EarningsPerShareDiluted. |
| Stockholders’ equity (FY2026 & FY2025) | facts.json; 10-K_2026-07-29.txt lines 5386–5395 | correct | FY2026: $442.387B; FY2025: $343.479B. Tag: StockholdersEquity. |
| Long-term debt, current portion | facts.json; 10-K_2026-07-29.txt lines 5124–5133 | correct (citation corrected) | $9.227B and $2.999B. Tag LongTermDebtCurrent. Final report range includes both years; original range did not. |
| Long-term debt, noncurrent | facts.json; 10-K_2026-07-29.txt lines 5208–5217 | correct (citation corrected) | $31.067B and $40.152B. Tag LongTermDebtNoncurrent. Final report range includes both years; original range did not. |
| Cash from operations | facts.json; 10-K_2026-07-29.txt lines 5796–5805 | correct (citation corrected) | $182.935B and $136.162B. Tag NetCashProvidedByUsedInOperatingActivities. Final report range includes both years; original range did not. |
| Additions to property and equipment | facts.json; 10-K_2026-07-29.txt lines 6062–6074 | correct (citation corrected) | $115.948B and $64.551B. Tag PaymentsToAcquirePropertyPlantAndEquipment. Final report range includes both years; original range did not. |
| Revenue growth | Arithmetic from printed inputs | correct | (331,839,000,000 − 281,724,000,000) / 281,724,000,000 = 17.7887%. |
| Operating margin | Arithmetic from printed inputs | correct | 155,237,000,000 / 331,839,000,000 = 46.7808%. |
| Return on average equity | Arithmetic from printed inputs | correct | 133,749,000,000 / ((442,387,000,000 + 343,479,000,000) / 2) = 34.0386%. |
| Debt to equity ratio | Arithmetic from printed inputs | correct | (9,227,000,000 + 31,067,000,000) / 442,387,000,000 = 9.1083%. |
| Free cash flow | Arithmetic from printed inputs | correct | 182,935,000,000 − 115,948,000,000 = $66,987,000,000. |
| Price to earnings (P/E) | Arithmetic from printed inputs | correct | $531.01 / $17.95 = 29.5827. Share price is external October 28, 2026 close. |
| Q1 FY2027 revenue quote | 8-K_Ex99.1_2026-10-28.txt line 9 | correct | “Revenue was $92.3 billion and increased 19%” matches. |
| Q1 FY2027 GAAP diluted EPS quote | 8-K_Ex99.1_2026-10-28.txt line 12 | correct | “Diluted earnings per share was $4.92 and increased 32% on a GAAP basis” matches. |
| Peer comparison (AAPL facts & margin) | AAPL_facts.json; Apple 2025 10-K (accession 0000320193-25-000079), period ending 2025-09-27 | correct | FY2025 revenue $416.161B and operating income $133.050B. Margin = 133,050,000,000 / 416,161,000,000 = 31.9708%. Tags RevenueFromContractWithCustomerExcludingAssessedTax and OperatingIncomeLoss. The saved 10-K table reports net sales $416,161m and operating income $133,050m (in millions; page 47). |

## Partner checks

1. **Q1 FY2027 revenue and diluted EPS quotes — correct.** Checked the saved Exhibit 99.1 text. Line 8 says the quarter ended September 30, 2026; line 9 gives revenue of $92.3 billion, up 19%; line 12 gives GAAP diluted EPS of $4.92, up 32%, and non-GAAP EPS of $4.89. The report quotes the requested GAAP figures accurately. The Exhibit 99.1 text itself does not contain the EDGAR accession header; the accession-number limitation below remains.
2. **Apple peer operating margin — correct.** Checked AAPL_facts.json against the saved Apple 2025 10-K. The filing’s page 47 segment table lists net sales of $416,161 million and operating income of $133,050 million for FY2025. These match the report’s facts and tags. Recalculation: 133,050 / 416,161 = 0.31970799… = 31.9708% (31.97% rounded). Both inputs use the same fiscal period and units, so the ratio is consistent.

## Remaining issues or limitations

- The 8-K accession 0001193125-26-436122 is not printed in the Exhibit 99.1 text; the report lists it, but this text alone cannot verify it.
- The $531.01 October 28, 2026 share price is an external close input, not a figure in the financial filings.
- The Apple statement references in the report point to Apple’s external EDGAR 10-K. The saved Apple filing text was also checked; its corresponding financial values appear in the FY2025 segment table on page 47.

## Review record

Student sign-off in the original review: Student (human sign-off), 2026-10-28.
Partner review completed by Shachi Kaushik. She personally checked both listed claims against the cited filings by hand on 2026-11-02. The two partner items are recorded above as correct.
