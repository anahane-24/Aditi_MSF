# Valuation Worksheet Inputs & Method Specification

**Team:** Three Checks — Aditi Nahane, Shachi, and Mrunalini  
**Course:** FIN 67110 Mastering AI for Finance  
**Lab Assignment:** Lab 07 (Your Investor) / Checkpoint 3  
**Framework:** Five-Year Owner-Cash-Flow DCF with Gordon-Growth Terminal Value

---

## 1. Valuation Method: Course Owner Cash Flow

Intrinsic value is estimated using the course-mandated formula for owner cash flow:

$$\text{Owner Cash Flow} = \text{Net Income} + \text{Depreciation} - \text{Capital Spending}$$

### Data Sourcing & Provenance
All inputs are extracted directly from audited SEC Form 10-K statements:
- **Net Income:** SEC XBRL tag `NetIncomeLoss`
- **Depreciation:** SEC XBRL tag `Depreciation`
- **Capital Spending (Capex):** SEC XBRL tag `PaymentsToAcquireProductiveAssets` or `PaymentsToAcquirePropertyPlantAndEquipment`
- **Diluted Shares Outstanding:** SEC XBRL tag `WeightedAverageNumberOfDilutedSharesOutstanding`
- **Stockholders' Equity:** SEC XBRL tag `StockholdersEquity` (including prior-year comparator to compute average equity for ROE)
- **Total Debt:** Sum of Current Debt (`LongTermDebtCurrent`) and Noncurrent Debt (`LongTermDebtNoncurrent`)

---

## 2. Parameter Assumptions & Rates

| Parameter | Bear Case (Conservative) | Base Case (Normalized) | Bull Case (Optimistic) |
|---|---|---|---|
| **5-Year Growth Rate ($g_1$)** | 4.0% | 7.0% | 10.0% |
| **Discount Rate ($r$)** | 10.0% | 9.0% | 8.5% |
| **Terminal Growth Rate ($g_2$)** | 2.0% | 2.5% | 3.0% |

### Valuation Formulas
1. **Present Value of 5-Year Cash Flows:**
   $$PV_{\text{explicit}} = \sum_{t=1}^{5} \frac{OCF_0 \times (1 + g_1)^t}{(1 + r)^t}$$
2. **Terminal Value (Gordon Growth):**
   $$TV_5 = \frac{OCF_5 \times (1 + g_2)}{r - g_2}$$
   $$PV(TV) = \frac{TV_5}{(1 + r)^5}$$
3. **Total Equity Value:**
   $$\text{Total Value} = PV_{\text{explicit}} + PV(TV)$$
4. **Owner-Cash-Flow Value Per Diluted Share:**
   $$IV_{\text{share}} = \frac{\text{Total Value}}{\text{Diluted Shares Outstanding}}$$
5. **Margin of Safety:**
   $$\text{Margin of Safety} = \frac{IV_{\text{base}} - \text{Current Market Price}}{IV_{\text{base}}} \times 100\%$$

---

## 3. Client Purchase Size & Conviction Rules

### Client Portfolio Size
- Dedicated Client Fund Assets: **$10,000,000 USD**

### Conviction Decision Logic
- **BUY:**
  - Market Price $\le 0.80 \times IV_{\text{base}}$ (Minimum **20.0% margin of safety**)
  - Return on Equity ($ROE$) $\ge 15.0\%$ (calculated using average stockholders' equity)
  - Debt-to-Equity $\le 0.75$
- **HOLD:**
  - Market Price is between $0.80 \times IV_{\text{base}}$ and $1.20 \times IV_{\text{base}}$
  - Stable business operations with non-negative Owner Cash Flow
- **SELL / AVOID:**
  - Market Price $> 1.20 \times IV_{\text{base}}$ (Overvalued)
  - Debt-to-Equity $> 1.00$ (Excessive balance sheet risk)
  - Negative trailing Owner Cash Flow

### Client Purchase Size Allocation ($10,000,000 Portfolio)
- **High Conviction (Tier 1):** Margin of Safety $\ge 30.0\%$ and Debt-to-Equity $\le 0.50$ $\rightarrow$ **5.0% allocation = $500,000 USD**
- **Moderate Conviction (Tier 2):** Margin of Safety $20.0\%$ to $29.9\%$ and Debt-to-Equity $\le 0.75$ $\rightarrow$ **2.5% allocation = $250,000 USD**
- **Sub-Threshold (Tier 3):** Margin of Safety $< 20.0\%$ $\rightarrow$ **0.0% allocation = $0.00 USD** (No purchase)

---

## 4. Single Deciding Number
The investor's conviction rating is governed exclusively by:
$$\text{Deciding Number} = \text{Margin of Safety Percentage} = \frac{IV_{\text{base}} - P_{\text{market}}}{IV_{\text{base}}} \times 100\%$$
