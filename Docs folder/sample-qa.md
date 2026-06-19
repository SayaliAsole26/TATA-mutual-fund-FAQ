# Sample Q&A

Example queries run against the **production API** on 19 Jun 2026.  
Live UI: https://tata-mutual-fund-faq.vercel.app

Each factual answer includes a **source link** to the Groww scheme page used.

---

## 1. Minimum SIP (factual answer)

**Query:** What is the minimum SIP for Tata ELSS?

**Scheme:** Tata ELSS Fund Direct Growth

**Answer:** Minimum SIP: ₹500.

**Source:** https://groww.in/mutual-funds/tata-elss-fund-direct-growth

**Last updated from sources:** 18 Jun 2026

---

## 2. Expense ratio (factual answer)

**Query:** What is the expense ratio of Tata Arbitrage Fund?

**Scheme:** Tata Arbitrage Fund Direct Growth

**Answer:** Expense ratio: 1.02%.

**Source:** https://groww.in/mutual-funds/tata-arbitrage-fund-direct-growth

**Last updated from sources:** 18 Jun 2026

---

## 3. Exit load (factual answer)

**Query:** What is the exit load on Tata Silver ETF FoF?

**Scheme:** Tata Silver ETF FoF Direct Growth

**Answer:** The exit load on Tata Silver ETF FoF is 0.5% if redeemed within 7 days.

**Source:** https://groww.in/mutual-funds/tata-silver-etf-fof-direct-growth

**Last updated from sources:** 18 Jun 2026

---

## 4. Lock-in period (factual answer)

**Query:** What is the lock-in period for Tata ELSS Fund?

**Scheme:** Tata ELSS Fund Direct Growth

**Answer:** ELSS lock-in: 3Y Lock-in.

**Source:** https://groww.in/mutual-funds/tata-elss-fund-direct-growth

**Last updated from sources:** 18 Jun 2026

---

## 5. Minimum investment (factual answer)

**Query:** What is the minimum investment for Tata Flexi Cap Fund?

**Scheme:** Tata Flexi Cap Fund Direct Growth

**Answer:** The minimum investment for Tata Flexi Cap Fund is ₹5,000 for lumpsum and ₹100 for SIP.

**Source:** https://groww.in/mutual-funds/tata-flexi-cap-fund-direct-growth

**Last updated from sources:** 18 Jun 2026

---

## 6. Benchmark (factual answer)

**Query:** What is the benchmark for Tata BSE Sensex Index Direct?

**Scheme:** Tata BSE Sensex Index Direct

**Answer:** Benchmark: BSE Sensex Total Return Index.

**Source:** https://groww.in/mutual-funds/tata-bse-sensex-index-direct

**Last updated from sources:** 18 Jun 2026

---

## 7. Exit load — large cap (factual answer)

**Query:** What is the exit load for Tata Large Cap Fund?

**Scheme:** Tata Large Cap Fund Direct Growth

**Answer:** The exit load for Tata Large Cap Fund is 0.50% if redeemed within 30 days.

**Source:** https://groww.in/mutual-funds/tata-large-cap-fund-direct-growth

**Last updated from sources:** 18 Jun 2026

---

## 8. Advisory refusal (guardrail)

**Query:** Should I invest in Tata Small Cap Fund?

**Response type:** `refusal` (reason: `advisory`)

**Answer:** I am a facts-only assistant and cannot provide investment advice, recommendations, or opinions. For general mutual fund education, please visit the AMFI Investor Corner.

**Source:** https://www.amfiindia.com/investor-corner

**Last updated from sources:** 19 Jun 2026

---

## 9. Scheme clarification (ambiguous query)

**Query:** What is the expense ratio?

**Response type:** `clarification`

**Answer:** Which Tata Mutual Fund scheme do you mean? For example: Tata Small Cap Fund Direct Growth, Tata Digital India Fund Direct Growth, Tata Silver ETF FoF Direct Growth, Tata Ethical Fund Direct Growth, …

**Source:** — (user must name a scheme)

---

## Reproduce locally

```bash
curl -X POST https://tata-mutual-fund-faq-production.up.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What is the minimum SIP for Tata ELSS?\"}"
```
