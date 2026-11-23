# Worksheet — Alphabet_Inc._20261122_174504_278128_Eastern Standard Time

Method: five-year owner-cash-flow DCF with Gordon-growth terminal value; 5-year projection. The rates come from the team-authored `config/valuation_worksheet_inputs.md`.

## Owner cash flow

Net income $132,170,000,000 + depreciation $21,136,000,000 - capital spending $91,447,000,000 = **$61,859,000,000**.

- Net income source: `NetIncomeLoss`; period end 2025-12-31; accession `0001652044-26-000018`; 10-K filed 2026-02-05.
- Depreciation source: `Depreciation`; period end 2025-12-31; accession `0001652044-26-000018`; 10-K filed 2026-02-05.
- Capital spending source: `PaymentsToAcquirePropertyPlantAndEquipment`; period end 2025-12-31; accession `0001652044-26-000018`; 10-K filed 2026-02-05.

## Value range

Formula: project owner cash flow for each year; discount each cash flow; calculate terminal value as final-year cash flow × (1 + terminal growth) / (discount rate - terminal growth); discount terminal value; add the present values; divide by diluted shares.

| Case | 5-year growth | Discount rate | Terminal growth | Owner-cash-flow value per diluted share |
|---|---:|---:|---:|---:|
| Bear | 4.0% | 10.0% | 2.0% | $70.16 |
| Base | 7.0% | 9.0% | 2.5% | $96.64 |
| Bull | 10.0% | 8.5% | 3.0% | $127.81 |

Diluted shares: 12,230,000,000; source `WeightedAverageNumberOfDilutedSharesOutstanding`; period end 2025-12-31; accession `0001652044-26-000018`; 10-K filed 2026-02-05.

This calculator uses the course definition of owner cash flow as an equity cash-flow proxy. It divides that value by diluted shares. It does not call the result enterprise value or subtract debt again. The course formula is simplified and does not include working-capital changes. The source file also lists terminal multiples; this implementation uses its explicit Gordon-growth formula and does not use those multiples.

Market close: $324.89 on 2026-10-28 (LSEG Data Library: TR.PriceClose). Margin of safety against base case: -236.19%. ROE using average equity: 35.70%. Debt/equity, including current and noncurrent debt: 11.69%.

Deciding number: Margin of Safety percentage against base-case value; measured value: -236.19%.

## Quantitative decision screen

Rule result: **Sell / Avoid**. Reason: At least one written Sell / Avoid condition is true. Allocation tier: none; allocation: 0.0%. Dollar purchase size: $0.00.

## Policy reconciliation status

The investor persona, valuation input specification, and calculator rules are fully reconciled on the course formula (net income + depreciation - capital spending), the 3-case DCF rates, the Margin of Safety deciding number, and the $10,000,000 USD client portfolio size.
