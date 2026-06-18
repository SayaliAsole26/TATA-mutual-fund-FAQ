# Problem Statement: Mutual Fund FAQ Assistant (Facts-Only Q&A)

## Overview

The objective of this project is to build a facts-only FAQ assistant for mutual fund schemes, using Groww as the reference product context. The assistant answers objective, verifiable queries related to mutual funds, retrieving information from a curated corpus of 15 Tata Mutual Fund scheme pages on Groww. Advisory refusals may reference official AMFI and SEBI educational resources.

The system strictly avoids providing investment advice, opinions, or recommendations. Every response must include a single, clear source link and adhere to defined constraints around clarity, accuracy, and compliance.

## Objective

Design and implement a lightweight Retrieval-Augmented Generation (RAG)-based assistant that:

- Answers factual queries about schemes
- Uses a curated corpus of official documents
- Provides concise, source-backed responses

### Target Users

- Retail investors comparing mutual fund schemes
- Customer support and content teams handling repetitive mutual fund queries

## Scope of Work

### 1. Corpus Definition

- **Selected AMC:** Tata Mutual Fund
- **Corpus size:** 15 curated scheme pages (Groww reference URLs)
- **Source type:** Groww mutual fund scheme pages, used as the reference product context for factual scheme data (expense ratio, exit load, minimum SIP, riskometer, benchmark, fund managers, etc.)

The corpus is limited to the following 15 URLs:

| # | Scheme | URL |
|---|--------|-----|
| 1 | Tata Small Cap Fund Direct Growth | https://groww.in/mutual-funds/tata-small-cap-fund-direct-growth |
| 2 | Tata Digital India Fund Direct Growth | https://groww.in/mutual-funds/tata-digital-india-fund-direct-growth |
| 3 | Tata Silver ETF FoF Direct Growth | https://groww.in/mutual-funds/tata-silver-etf-fof-direct-growth |
| 4 | Tata Ethical Fund Direct Growth | https://groww.in/mutual-funds/tata-ethical-fund-direct-growth |
| 5 | Tata Arbitrage Fund Direct Growth | https://groww.in/mutual-funds/tata-arbitrage-fund-direct-growth |
| 6 | Tata Nifty Capital Markets Index Fund Direct Growth | https://groww.in/mutual-funds/tata-nifty-capital-markets-index-fund-direct-growth |
| 7 | Tata Resources & Energy Fund Direct Growth | https://groww.in/mutual-funds/tata-resources-energy-fund-direct-growth |
| 8 | Tata ELSS Fund Direct Growth | https://groww.in/mutual-funds/tata-elss-fund-direct-growth |
| 9 | Tata Multicap Fund Direct Growth | https://groww.in/mutual-funds/tata-multicap-fund-direct-growth |
| 10 | Tata Ultra Short Term Fund Direct Growth | https://groww.in/mutual-funds/tata-ultra-short-term-fund-direct-growth |
| 11 | Tata Mid Cap Direct Plan Growth | https://groww.in/mutual-funds/tata-mid-cap-direct-plan-growth |
| 12 | Tata Flexi Cap Fund Direct Growth | https://groww.in/mutual-funds/tata-flexi-cap-fund-direct-growth |
| 13 | Tata Large Cap Fund Direct Growth | https://groww.in/mutual-funds/tata-large-cap-fund-direct-growth |
| 14 | Tata Floater Fund Direct Growth | https://groww.in/mutual-funds/tata-floater-fund-direct-growth |
| 15 | Tata BSE Sensex Index Direct | https://groww.in/mutual-funds/tata-bse-sensex-index-direct |

#### Daily Ingestion Schedule

An offline ingestion pipeline refreshes the corpus from the 15 Groww URLs above. A **daily scheduler** triggers this job at **10:00 IST** (Indian Standard Time, `Asia/Kolkata`) to fetch the latest scheme data, re-index content, and update `last_ingested_at` timestamps used in response footers.

| Aspect | Requirement |
|--------|-------------|
| **Schedule** | Every day at 10:00 IST |
| **Scope** | All 15 corpus URLs |
| **Purpose** | Keep factual answers aligned with the latest available scheme information |

### 2. FAQ Assistant Requirements

The assistant must:

- Answer facts-only queries, such as:
  - Expense ratio of a scheme
  - Exit load details
  - Minimum SIP amount
  - ELSS lock-in period
  - Riskometer classification
  - Benchmark index
  - Process to download statements or capital gains reports
  - Funds management information
- Ensure:
  - Each response is limited to a maximum of 3 sentences
  - Each response includes exactly one citation link
  - Each response includes a footer:
    - `Last updated from sources: <date>`

### 3. Refusal Handling

The assistant must refuse non-factual or advisory queries, such as:

- "Should I invest in this fund?"
- "Which fund is better?"

Refusal responses should:

- Be polite and clearly worded
- Reinforce the facts-only limitation
- Provide a relevant educational link (e.g., AMFI or SEBI resource)

### 4. User Interface (Minimal)

The solution should include a simple interface with:

- A welcome message
- Three example questions
- A visible disclaimer:

  > Facts-only. No investment advice.

## Constraints

### Data and Sources

- Current implementation corpus: the 15 Tata Mutual Fund scheme pages on Groww (see [Corpus Definition](#1-corpus-definition))
- Corpus data is refreshed daily via the offline ingestion pipeline, triggered by a scheduler at **10:00 IST**
- Responses must cite the relevant scheme page from the corpus as the source link
- Do not use third-party blogs or other aggregator websites beyond the defined corpus
- For advisory refusals and educational context, prefer official AMFI/SEBI resources where applicable

### Privacy and Security

- Do not collect, store, or process:
  - PAN or Aadhaar numbers
  - Account numbers
  - OTPs
  - Email addresses or phone numbers

### Content Restrictions

- No investment advice or recommendations
- No performance comparisons or return calculations
- For performance-related queries, provide a link to the official factsheet only

### Transparency

- Responses must be short, factual, and verifiable
- Every answer must include a source link and last updated date

## Expected Deliverables

### 1. README Document

- Setup instructions
- Selected AMC and schemes
- Architecture overview (RAG approach, daily ingestion at 10:00 IST)
- Known limitations

### 2. Disclaimer Snippet

> Facts-only. No investment advice.

## Success Criteria

- Accurate retrieval of factual mutual fund information
- Strict adherence to facts-only responses
- Consistent inclusion of valid source citations
- Proper refusal of advisory queries
- Clean, minimal, and user-friendly interface

## Summary

The goal is to build a trustworthy, transparent, and compliant mutual fund FAQ assistant that prioritizes accuracy over intelligence. The system should ensure that users receive only verified, source-backed financial information, without any advisory bias or speculative content.
