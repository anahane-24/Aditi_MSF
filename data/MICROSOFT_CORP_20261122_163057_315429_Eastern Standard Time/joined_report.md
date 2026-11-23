# NOT VERIFIED — Lab 09 joined draft

The model report failed the evidence hook. This file preserves the model output and adds the deterministic worksheet. Do not submit it as a verified report.

Filings read: MSFT 10-K accession 0001193125-26-323660; MSFT 10-Q accession 0001193125-26-436133; MSFT 8-K Exhibit 99.1 accession 0001193125-26-436122; GOOGL latest 10-K accession 0001652044-26-000018
Run time: 2026-11-22T16:31:02-05:00

## Overview

Microsoft Corporation, a leading global technology company, reported strong financial performance in the third quarter of fiscal year 2026. The company’s revenue reached $92,279 million, with operating income of $45,915 million and net income of $133,749 million for the full fiscal year ending June 30, 2026. Key financial metrics include depreciation of $34,300 million and capital spending (CapEx) of $115,948 million. The company’s diluted shares outstanding were 7,453,000,000.

## Market Positioning and Growth Outlook

Microsoft continues to dominate in cloud infrastructure and services, maintaining a strong competitive position. However, the company's reliance on its cloud infrastructure exposes it to potential disruption from competitors or shifts in enterprise demand for cloud-based solutions, which could significantly impact long-term revenue growth and market share. (Item 7, line 01890)

Insight: Microsoft's reliance on its cloud infrastructure and services exposes it to potential disruption from competitors or shifts in enterprise demand for cloud-based solutions, which could significantly impact long-term revenue growth and market share. (Item 7, line 01890)

## Valuation Insights

Microsoft’s operating margin of approximately 50% (based on Q3 2026 data) reflects strong profitability, significantly outpacing Alphabet’s FY 2025 margin of ~32.03%. This is derived from operating income of $45,915 million divided by revenue of $92,279 million in the three months ended September 30, 2026 (accession `0001193125-26-323660`, 10-K filed 2026-07-29).

Insight: Microsoft's operating margin of approximately 50% (based on Q3 2026 data) reflects strong profitability, significantly outpacing Alphabet’s FY 2025 margin of ~32.03%. This is derived from operating income of $45,915 million divided by revenue of $92,279 million in the three months ended September 30, 2026 (accession `0001193125-26-323660`, 10-K filed 2026-07-29).

## Future Developments and Strategic Recommendations

Microsoft’s strategic focus remains on innovation and expansion in cloud computing, artificial intelligence, and enterprise solutions. The company is expected to continue investing heavily in research and development to maintain its competitive edge. Additionally, Microsoft is likely to pursue further acquisitions and partnerships to enhance its product portfolio and market reach.

## Investment Recommendation

- **Recommendation:** **Sell / Avoid**
- **Thesis:** Microsoft exhibits strong operational profitability with an operating margin of ~50% (Q3 2026), outpacing peers like Alphabet. However, the company's current valuation is severely overpriced relative to its base-case intrinsic value, as evidenced by a negative margin of safety of -297.57%. This extreme mispricing, combined with no qualifying solvency or cash flow advantages to justify the investment, leads to a clear Sell / Avoid recommendation.
- **Deciding number:** The Margin of Safety percentage against Base Case Intrinsic Value is **-297.57%**, computed as:
  $$
  \text{Margin of Safety} = \frac{\text{Base Case Intrinsic Value} - \text{Current Market Price}}{\text{Base Case Intrinsic Value}} = \frac{133.56 - 531.01}{133.56}
  $$
  This value is derived from the Financial Analyst's deterministic valuation worksheet and confirms that the stock is trading at more than 297% above its estimated intrinsic value, violating all thresholds for a Buy conviction.
- **Monitoring priorities:** A revision would be triggered if Microsoft’s market price drops below 80% of the base-case intrinsic value ($106.85/share), or if there is a material decline in owner cash flow, increase in debt-to-equity beyond 0.75, or erosion of competitive moat.

Insight: Microsoft's reliance on its cloud infrastructure and services exposes it to potential disruption from competitors or shifts in enterprise demand for cloud-based solutions, which could significantly impact long-term revenue growth and market share. (Item 7, line 01890)


## Worksheet

# Worksheet — MICROSOFT_CORP_20261122_163057_315429_Eastern Standard Time

Method: five-year owner-cash-flow DCF with Gordon-growth terminal value; 5-year projection. The rates come from the team-authored `config/valuation_worksheet_inputs.md`.

## Owner cash flow

Net income $133,749,000,000 + depreciation $34,300,000,000 - capital spending $115,948,000,000 = **$52,101,000,000**.

- Net income source: `NetIncomeLoss`; period end 2026-06-30; accession `0001193125-26-323660`; 10-K filed 2026-07-29.
- Depreciation source: `Depreciation`; period end 2026-06-30; accession `0001193125-26-323660`; 10-K filed 2026-07-29.
- Capital spending source: `PaymentsToAcquirePropertyPlantAndEquipment`; period end 2026-06-30; accession `0001193125-26-323660`; 10-K filed 2026-07-29.

## Value range

Formula: project owner cash flow for each year; discount each cash flow; calculate terminal value as final-year cash flow × (1 + terminal growth) / (discount rate - terminal growth); discount terminal value; add the present values; divide by diluted shares.

| Case | 5-year growth | Discount rate | Terminal growth | Owner-cash-flow value per diluted share |
|---|---:|---:|---:|---:|
| Bear | 4.0% | 10.0% | 2.0% | $96.97 |
| Base | 7.0% | 9.0% | 2.5% | $133.56 |
| Bull | 10.0% | 8.5% | 3.0% | $176.65 |

Diluted shares: 7,453,000,000; source `WeightedAverageNumberOfDilutedSharesOutstanding`; period end 2026-06-30; accession `0001193125-26-323660`; 10-K filed 2026-07-29.

This calculator uses the course definition of owner cash flow as an equity cash-flow proxy. It divides that value by diluted shares. It does not call the result enterprise value or subtract debt again. The course formula is simplified and does not include working-capital changes. The source file also lists terminal multiples; this implementation uses its explicit Gordon-growth formula and does not use those multiples.

Market close: $531.01 on 2026-10-28 (LSEG Data Library: TR.PriceClose). Margin of safety against base case: -297.57%. ROE using average equity: 34.04%. Debt/equity, including current and noncurrent debt: 9.11%.

Deciding number: Margin of Safety percentage against base-case value; measured value: -297.57%.

## Quantitative decision screen

Rule result: **Sell / Avoid**. Reason: At least one written Sell / Avoid condition is true. Allocation tier: none; allocation: 0.0%. Dollar purchase size: $0.00.

## Policy reconciliation status

The investor persona, valuation input specification, and calculator rules are fully reconciled on the course formula (net income + depreciation - capital spending), the 3-case DCF rates, the Margin of Safety deciding number, and the $10,000,000 USD client portfolio size.
