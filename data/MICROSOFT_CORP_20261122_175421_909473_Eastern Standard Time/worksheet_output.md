# Worksheet — MICROSOFT_CORP_20261122_175421_909473_Eastern Standard Time

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
