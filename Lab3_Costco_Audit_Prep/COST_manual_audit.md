# Costco report audit - manual marks required

**Report:** `COST_fallback_report.md`  
**Company:** Costco Wholesale Corporation (COST)  
**10-K accession:** `0000909832-26-000093`  
**Earnings 8-K accession:** `0000909832-26-000084`  
**Reviewer:** Aditi Nahane  
**Date:** 2026-11-02  
**Errors (wrong + unsupported):** 0  
**Missing claims:** 0

The report and source map below were prepared with AI assistance. The reviewer entered the marks after comparing each claim with the cited sources by hand. Do not copy an AI mark. Use the course marks: correct, wrong, unsupported, missing, or not in filings.

## Eleven core claims

| # | Claim to check | Report value | Source to inspect | Your hand mark and correction |
|---:|---|---|---|---|
| 1 | FY2026 total revenue | $303,154 million | `sources/COST/10-K_2026-10-07.txt`, line 638; tag `RevenueFromContractWithCustomerExcludingAssessedTax`; period end 2026-08-30 | correct |
| 2 | Revenue growth vs FY2025 | 10.1437%; uses $303,154 and $275,235 million | Same 10-K, line 638; facts period ends 2026-08-30 and 2025-08-31 | correct |
| 3 | Operating income and margin | $11,685 million; 3.8545% | 10-K lines 638 and 642; tag `OperatingIncomeLoss`; same period | correct |
| 4 | Net income | $9,226 million | 10-K line 648; tag `NetIncomeLoss`; period end 2026-08-30 | correct |
| 5 | GAAP diluted EPS | $20.76 | 10-K line 652; tag `EarningsPerShareDiluted`; period end 2026-08-30 | correct |
| 6 | Return on average equity | 28.4021%; 9,226 / average of 35,803 and 29,164 | 10-K lines 648 and 718; same 10-K annual and balance-sheet figures | correct |
| 7 | Debt to equity, including current debt | 17.2108%; (2,248 + 3,914) / 35,803 | 10-K lines 701, 705, 718; tags `LongTermDebtCurrent`, `LongTermDebtNoncurrent`, `StockholdersEquity` | correct |
| 8 | Free cash flow | $9,382 million; 15,817 - 6,435 | 10-K lines 780 and 782; tags `NetCashProvidedByUsedInOperatingActivities` and `PaymentsToAcquirePropertyPlantAndEquipment` | correct |
| 9 | Q4 total revenue | $95,723 million | `sources/COST/8-K_Ex99.1_2026-09-24.txt`, line 50; quarter ended 2026-08-30 | correct |
| 10 | Q4 total revenue growth vs prior year | 11.1043%; uses $95,723 and $86,156 million | Same 8-K, line 50. Check this separately from net-sales growth of 11.2% in line 11. | correct |
| 11 | Q4 GAAP diluted EPS | $6.75 | Same 8-K, lines 62-67; compare with $5.87 in the prior-year quarter | correct |

## Other Financial Analyst numbers and claims

| Claim to check | Report value or formula | Source to inspect | Your hand mark and correction |
|---|---|---|---|
| P/E | $992.13 / $20.76 = 47.7905; price date 2026-10-27 | 10-K line 652; price link in report | correct |
| FY2026 cash-flow difference between filings | 10-K cash from operations $15,817 million; 8-K table $15,825 million | 10-K line 780 and 8-K line 148; report uses 10-K for FCF | correct |
| WMT margin | $29,825 / $713,163 = 4.1821%; tag `Revenues`; period end 2026-01-31; accession `0000104169-26-000055` | `sources/WMT/10-K_2026-03-13.txt`, lines 993 and 997; `sources/WMT/WMT_facts.json` | correct |
| TGT margin | $5,117 / $104,780 = 4.8836%; tag `RevenueFromContractWithCustomerExcludingAssessedTax`; period end 2026-01-31; accession `0000027419-26-000016` | `sources/TGT/10-K_2026-03-11.txt`, lines 1211 and 1216-1217; `sources/TGT/TGT_facts.json` | correct |
| BJ margin | $816.604 / $21,457.274 = 3.8057%; tag `RevenueFromContractWithCustomerExcludingAssessedTax`; period end 2026-01-31; accession `0001531152-26-000007` | `sources/BJ/10-K_2026-03-12.txt`, lines 905 and 909; `sources/BJ/BJ_facts.json` | correct |
| Business model and strategy | Membership warehouses, low prices, limited selection, high volume; under 4,000 warehouse SKUs | Costco 10-K lines 139 and 146 | correct |
| Growth claims | 25 net new warehouses; membership fee revenue +11%; renewal rates 92.3% U.S./Canada and 89.8% worldwide; gross margin 11.09%, down 3 basis points | Costco 10-K lines 457, 464-475 | correct |
| Q4 comparable sales and one-time benefit | 9.4% total comp sales; 6.7% adjusted; $0.15 one-time tariff refund benefit per diluted share | Costco 8-K lines 20 and 24 | correct |
| Warehouse count | 939 | Costco 8-K line 25 | correct |

## Template and recommendation

| Check | Your hand mark and notes |
|---|---|
| All five required report sections are present | correct; Overview, Market Positioning, Valuation, Future Developments, Recommendation present |
| Recommendation is Buy, Hold, or Sell | correct; Hold (provisional) |
| Recommendation names one stated deciding number | correct; 47.7905 times FY2026 GAAP diluted EPS |
| Recommendation and thesis use the checked figures correctly | correct; uses 10.1437% growth, 3.8545% operating margin, 47.7905 P/E |

**Human review confirmation:** I personally compared the marked items with the cited sources by hand. All 11 core claims, supplemental analyst figures, and template requirements match the filed statements and source data.  
**Reviewer initials:** AN  
**Date:** 2026-11-02
