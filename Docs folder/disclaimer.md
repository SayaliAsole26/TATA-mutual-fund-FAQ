# Disclaimer snippet (UI)

This is the **exact disclaimer text** shown in the chat UI, rendered by [`frontend/src/components/Disclaimer.tsx`](../frontend/src/components/Disclaimer.tsx). It appears above the input bar on every screen.

---

## Primary UI disclaimer (sticky above input)

```
Facts-only. No investment advice. Mutual fund investments are subject to market risks. Read all scheme related documents carefully.
```

**Component:** `Disclaimer` — left border accent (`border-secondary-container`), warning icon, monospace body text.

---

## Welcome screen scope text

Shown on the empty chat state ([`frontend/src/components/Welcome.tsx`](../frontend/src/components/Welcome.tsx)):

```
Ask objective questions about 15 Tata Mutual Fund schemes on Groww — expense ratio, minimum SIP, exit load, fund managers, benchmark, and more. I provide brief, verified facts with a source link below each answer.
```

---

## Refusal template (advisory / out of scope)

When the user asks for investment advice, the assistant returns a refusal card labelled **Information only**. Example body:

```
I am a facts-only assistant and cannot provide investment advice, recommendations, or opinions. For general mutual fund education, please visit the AMFI Investor Corner.
```

**Educational link:** https://www.amfiindia.com/investor-corner

---

## README / documentation disclaimer

From the project [README](../README.md):

> This assistant shares verified factual information from official scheme sources. It does **not** provide investment advice, recommendations, or performance forecasts. Mutual fund investments are subject to market risks. Read all scheme-related documents carefully.

**Educational links:**

- [AMFI Investor Corner](https://www.amfiindia.com/investor-corner)  
- [SEBI Investor Education](https://investor.sebi.gov.in)

---

## Copy-paste snippet (for submissions / reports)

> **Facts-only. No investment advice.**  
> This assistant answers objective questions about 15 Tata Mutual Fund schemes using verified information from Groww scheme pages. It does not provide investment recommendations, performance predictions, or personalised advice. Mutual fund investments are subject to market risks. Read all scheme related documents carefully.
