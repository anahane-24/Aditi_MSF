# Spinoff Factor List

**Author:** Aditi Nahane  
**Course:** FIN 67110 Mastering AI for Finance, Daniels School of Business, Purdue University  
**Topic:** U.S. Corporate Spinoff Screening & Ranking (Form 10 Registrations)  
**Primary Sources:**
- Joel Greenblatt, *You Can Be a Stock Market Genius* (1997), Chapter 3: "Chips off the Old Stock: Spinoffs, Partial Spinoffs, and Rights Offerings"
- Seth Klarman, *Margin of Safety* (1991), Chapter 10: "Portfolio Management and Trading - Spinoffs"

---

## 1. Overview of Screening Model

Spinoffs generate abnormal risk-adjusted returns primarily due to structural institutional inefficiencies rather than immediate operational changes. When a parent company distributes shares of a newly independent subsidiary to its existing shareholders, institutional shareholders frequently sell the spun-off shares indiscriminately regardless of underlying value.

Our screening model applies a **90-day post-distribution window** (`window_days: 90`) to identify and rank attractive spinoff opportunities emerging from EDGAR Form 10 filings (`10-12B` and `10-12G`).

---

## 2. Declared Factor Table

| Factor Name | Metric Field | Predicted Direction | Source Chapter | Threshold | Weight | Economic Rationale |
|---|---|---|---|---|---|---|
| **Post-Distribution Selling Pressure** | `window_return` | **Lower** | Greenblatt Chapter 3 | `<= 0.00%` | 25.0 pts | Forced institutional selling temporarily depresses prices during the first 30–90 days, creating a favorable margin of safety. |
| **Spinoff Relative Capitalization Size** | `relative_size_ratio` | **Lower** | Greenblatt Chapter 3 | `<= 0.20` | 25.0 pts | When the spinoff is under 20% of the parent company's market capitalization, large institutions routinely dump the position because it is too small to affect portfolio returns. |
| **Clean Spinoff Balance Sheet** | `debt_to_equity` | **Lower** | Klarman Chapter 10 | `<= 0.50` | 25.0 pts | Parent corporations sometimes load subsidiaries with parent debt prior to separation. Conservative leverage (D/E under 50%) ensures financial solvency and owner cash flow protection. |
| **Insider Ownership & Alignment** | `insider_ownership_pct` | **Higher** | Greenblatt Chapter 3 | `>= 5.0%` | 25.0 pts | Significant stock or option ownership by officers and directors of the new entity aligns management incentives with long-term equity appreciation. |

---

## 3. Factor Analysis and Filing Evidence

### Factor 1: Post-Distribution Selling Pressure Window
- **Field:** `window_return` (calculated as `(Price_t / Price_0) - 1` across `window_days`)
- **Predicted Direction:** Lower (threshold `<= 0.00`)
- **Source:** Greenblatt, Chapter 3
- **Mechanics:** Following the distribution date, index funds and institutional managers constrained by market-cap minimums or investment mandates sell the spun-off entity automatically. A negative or flat return within the initial 90-day window confirms that indiscriminate selling has occurred, creating mispricing before value investors step in.

### Factor 2: Spinoff Relative Capitalization Size
- **Field:** `relative_size_ratio` (Spinoff market capitalization / Parent market capitalization)
- **Predicted Direction:** Lower (threshold `<= 0.20`)
- **Source:** Greenblatt, Chapter 3
- **Mechanics:** If a $20 billion parent spins off a $1 billion subsidiary (a 5% relative size), an institutional manager holding a 2% parent position receives a spinoff position worth 0.1% of their portfolio. The friction of researching, tracking, and maintaining a 10-basis-point position incentivizes the manager to sell immediately, generating mispricing.

### Factor 3: Clean Balance Sheet Leverage
- **Field:** `debt_to_equity` (Total debt / Stockholders' equity from initial balance sheet)
- **Predicted Direction:** Lower (threshold `<= 0.50`)
- **Source:** Klarman, Chapter 10
- **Mechanics:** Klarman warns that parent companies frequently extract special cash dividends funded by debt loaded onto the spinoff just before separation. A low debt-to-equity ratio ensures the company retains free cash flow to invest in its core business rather than servicing parent legacy liabilities.

### Factor 4: Insider Ownership and Direct Incentive Alignment
- **Field:** `insider_ownership_pct` (Management and director beneficial ownership percentage)
- **Predicted Direction:** Higher (threshold `>= 0.05` or 5.0%)
- **Source:** Greenblatt, Chapter 3
- **Mechanics:** In Form 10 Information Statements (Item 4 or Security Ownership of Certain Beneficial Owners and Management), filings disclose executive compensation agreements and stock holdings. When management's personal net worth is levered to the spun-off equity, management works vigorously to unlock value and optimize operations.

---

## 4. Screening Execution Rules

1. **Screen Window:** 90 calendar days post-distribution date.
2. **Scoring Scale:** 0 to 100 points (4 factors × 25 points each).
3. **Data Completeness Constraint:** If a factor's feature data is unavailable in the filing or market data, the candidate is classified as `unranked` with the missing data fields explicitly cited.
