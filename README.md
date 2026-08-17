# AI Product Ops Research Agent

An AI-powered research agent that automatically investigates 100 applications for API access, authentication, developer availability, MCP support, buildability, blockers, and evidence, then generates a data-driven HTML case study.

---

## 🎯 Overview

Researching API surfaces and integration viability across 100 different applications manually is incredibly time-consuming and prone to human error. This project automates the product operations research process by combining targeted web search, web crawling, and AI-powered data extraction. The agent produces a structured dataset of API capabilities and outputs a professional HTML case study that highlights integration readiness, blockers, and clear patterns across the ecosystem.

---

## ✨ What the Agent Produces

For each application, the agent extracts structured research fields validated against a strict Pydantic schema:

| Research Area | Description |
|---|---|
| Category | Application category |
| Description | One-line application description |
| Authentication | OAuth2, API key, Basic, token, etc. |
| Developer Access | self-serve-free, self-serve-trial, paid-gated, partner-gated, contact-sales |
| API Available | Boolean flag for public API presence |
| API Type | REST, GraphQL, SDK, CLI, Webhook, etc. |
| API Breadth | broad, moderate, narrow, none |
| MCP Status | official, community, mentioned, none |
| Buildability | ready, buildable, partial, blocked |
| Blocker | Main integration blocker (if any) |
| Evidence | Source URLs and supporting claims/snippets |
| Confidence | high, medium, low |
| Manual Review | Whether extraction failed and requires manual review |

---

## 🧠 How It Works


flowchart LR
    A[README: 100 Apps]
    B[Tavily Search]
    C[Web Crawler]
    D[Gemma 4 26B]
    E[Pydantic Validation]
    F[Persist Results]
    G[Verification]
    H[Pattern Analysis]
    I[HTML Case Study]

    A --> B --> C --> D --> E --> F --> G --> H --> I
```

1. **README Parsing:** Parses the local README table to extract up to 100 application targets.
2. **Tavily Search:** Runs 4 targeted queries per app (docs, auth, pricing, MCP) to find relevant sources.
3. **Web Crawler:** Fetches HTML via `httpx` and extracts clean text using `trafilatura` (falling back to `BeautifulSoup`).
4. **Gemma 4 26B:** A self-hosted Gemma 4 26B model extracts structured API/integration facts into JSON format.
5. **Pydantic Validation:** Validates the model output against a strict predefined schema.
6. **Persist Results:** Saves extracted data to JSON after each app to allow resuming on failure.
7. **Verification:** Cross-checks key claims using secondary searches and validates evidence URLs.
8. **Pattern Analysis:** Aggregates findings to identify easy wins, outreach targets, and category trends.
9. **HTML Case Study:** Generates a visually rich, timestamped HTML report detailing the findings.

---

## 🏗️ Project Structure

```text
ai-product-ops-research-agent/
├── README.md           # The root app list and documentation
├── .env.example        # Template for required API keys and URLs
├── requirements.txt    # Python dependencies
├── src/
│   └── agent/
│       ├── main.py     # CLI entry point and pipeline orchestration
│       ├── models.py   # Pydantic schemas for structured extraction
│       ├── search.py   # Tavily-powered search logic
│       ├── crawler.py  # HTTP fetching and text extraction
│       ├── extractor.py# Gemma LLM prompt generation and JSON parsing
│       ├── verify.py   # Automated claim checking and human sample generation
│       ├── analyze.py  # Aggregation of results and trend analysis
│       └── report.py   # HTML case study generator
├── data/               # Output directory for raw JSON results
└── reports/            # Output directory for HTML case studies
```

---

## 🔎 Research Process

```text
App
 ↓
Search relevant documentation (4 targeted Tavily queries)
 ↓
Select sources (top 8 results deduplicated)
 ↓
Crawl/extract webpage content (up to 3 accessible pages, max 12,000 chars)
 ↓
Gemma extracts structured facts
 ↓
Pydantic validates the result (up to 3 retries on invalid JSON)
 ↓
Evidence is stored (alongside extracted claims)
 ↓
Verification checks claims (via secondary Tavily searches)
 ↓
Result contributes to aggregate analysis
```

---

## 📊 Analysis & Insights

The system aggregates the individual research results to identify broad ecosystem patterns, including:

* Authentication distribution (OAuth vs API keys, etc.)
* Developer access (self-serve vs gated access models)
* API types (REST, GraphQL, SDKs)
* API breadth 
* MCP adoption (official vs community)
* Overall buildability for AI agents
* Common blockers requiring outreach
* Category-level trends and dominant access models
* Easy wins (public API + self-serve + broad breadth)
* Outreach candidates (gated/blocked applications)

---

## ✅ Verification

The pipeline employs a two-tiered verification strategy implemented in `verify.py`.

### Automated verification

The software automatically performs two checks:
1. **Initial Accuracy:** Checks if the gathered evidence URLs are live and accessible.
2. **Final Accuracy:** Performs targeted secondary Tavily searches to cross-check critical claims (like buildability and access) against official documentation.

### Human verification

Human verification sample is prepared for manual review (a diverse 12-app sample); no human accuracy is claimed until the sample has actually been reviewed.

---

## 📄 Final Case Study

The structured JSON results and aggregate analysis are transformed into a professional, self-contained HTML case study.

The final report (implemented in `report.py`) contains:
* Key findings and summary metrics
* Interactive SVG bar charts for pattern analysis
* Category-level breakdown tables
* Easy-win and outreach candidate identification
* Accuracy tracking (before/after automated verification)
* Automated hits and misses
* A fully searchable 100-app research matrix
* Links to verified evidence URLs

Reports are saved to `reports/index.html` (latest) and timestamped as `reports/report_<timestamp>.html`.

---

## 🚀 Getting Started

### Clone

```bash
git clone https://github.com/raahulmaurya1/Ai_Product_Ops_Agent.git
cd Ai_Product_Ops_Agent
```

### Virtual environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Environment

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Set the required variables:

```env
GEMMA_API_URL=https://your-ngrok-url.ngrok-free.app
GEMMA_API_KEY=your-api-key-if-any
GEMMA_MODEL=gemma-4-26b
TAVILY_API_KEY=tvly-your-api-key
```

---

## ▶️ Running the Agent

### Quick test

Process just a small subset (default 3 apps) to validate the pipeline:

```bash
python -m src.agent.main --limit 3
```

### Full 100-app research

Process the complete 100-app research set (resumes automatically if previously interrupted):

```bash
python -m src.agent.main --all
```

### Verification

Run the automated verification pass on already saved results:

```bash
python -m src.agent.main --verify
```

### Report generation

Generate the HTML case study from already saved results without re-running the crawler:

```bash
python -m src.agent.main --report
```

---

## 📁 Output

The agent generates data artifacts in two main directories:

```text
data/
├── results.json        # The raw, Pydantic-validated JSON array for all processed apps
└── verification.json   # Accuracy metrics, hits/misses, and human review sample

reports/
├── index.html                  # Always points to the latest generated case study
└── report_<timestamp>.html     # Timestamped historical HTML report
```

The implementation preserves previous HTML reports alongside the `index.html` file.

---

## 🧩 Engineering Decisions

### Search vs Crawling
Tavily is used for discovery (finding the right documentation URLs), while `httpx` + `trafilatura` are used for robust content extraction. This separation prevents wasting expensive API calls on raw content fetching.

### Structured AI Extraction
A self-hosted Gemma 4 26B model acts purely as a structured data extractor. It translates noisy, unstructured web HTML into clean JSON fields.

### Pydantic Validation
Using Pydantic guarantees that the model's JSON output perfectly conforms to our strict schema before it enters our dataset, ensuring downstream analysis doesn't break due to LLM hallucinations.

### Evidence
Source URLs and claims are stored alongside every extracted result, ensuring all findings trace back to verifiable documentation.

### Verification
Verification is separated from initial extraction (and triggered post-run) to allow independent analysis of the model's reliability without slowing down the core data-gathering loop.

### Persistence
The pipeline automatically writes to `results.json` after every app. If a crash or rate limit occurs, running the script again seamlessly resumes from the last unprocessed app.

---

## ⚡ Key Design Principles

* Evidence-first research
* Structured outputs
* No fabricated findings
* Failure-tolerant crawling
* Explicit verification
* Data-driven reporting
* Reproducible execution

---

## ⚠️ Limitations

* Sites that aggressively block automated crawling (HTTP 4xx/5xx) are skipped and marked for manual review.
* JavaScript-heavy documentation portals that fail standard HTTP scraping may yield empty results.
* The system relies heavily on a self-hosted Gemma LLM endpoint; latency or timeouts at this endpoint will impact the pipeline.
* Claims are only as accurate as the first page of the public documentation; deeply gated developer access cannot be scraped.

---

## 🔮 Future Improvements

* Browser-based crawling (e.g., Playwright) to tackle JavaScript-heavy documentation (NOT currently implemented).
* Parallelized crawling and extraction for much faster batch processing (NOT currently implemented).
* Persistent database storage (e.g., PostgreSQL/SQLite) instead of flat JSON files (NOT currently implemented).

---

## 🎤 How I Would Explain This Project

> I built an automated product research agent that parses 100 applications, discovers relevant developer documentation using Tavily, crawls the sources via HTTP, uses a self-hosted Gemma model to extract structured API/integration information, strictly validates the output with Pydantic, stores evidence, independently verifies the findings, aggregates the results to identify patterns, and finally generates a comprehensive HTML case study.

### Likely Interview Discussion Points:

* **Why Tavily?** It's highly optimized for returning clean, relevant links and snippets compared to generic search APIs, which helps pinpoint API documentation faster.
* **Why an LLM for research extraction?** Documentation schemas vary wildly across 100 different companies. An LLM acts as a semantic parser that normalizes chaotic text into a unified structure.
* **How are hallucinations reduced?** We provide explicit instruction to return "unknown" rather than guessing, and we enforce a strict Pydantic schema with hardcoded enums.
* **Why Pydantic?** It acts as an unbreakable guardrail, ensuring we never pollute our dataset with malformed or unexpectedly formatted JSON.
* **How is evidence preserved?** For every data point, the crawler retains the exact source URL and the LLM explicitly returns the link as a piece of evidence.
* **How does verification work?** `verify.py` ensures the evidence URLs are accessible, and runs secondary searches to cross-check extracted facts against official documentation.
* **How are patterns calculated?** `analyze.py` aggregates frequency counts across all verified results to identify easy wins, blockers, and category distribution.
* **How is the HTML report generated?** A pure Python script (`report.py`) injects the analyzed metrics into a self-contained HTML template with inline SVG charts, no heavy frontend frameworks required.
