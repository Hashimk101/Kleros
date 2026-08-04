# 🏛️ KLEROS: Autonomous Discovery Agent for Free AI Resources

**Kleros** is an autonomous, on-demand discovery agent that finds, extracts, validates, and caches free LLM APIs, IDE credits, and chat subscriptions for students and developers.

---

## 🌟 Key Features

- **🔍 Multi-Source Search Router**: Primary search via DuckDuckGo with SearXNG fallback rotation.
- **📄 Clean Content Extraction**: Web page markdown rendering powered by Jina Reader API (`https://r.jina.ai/`).
- **🧠 LLM Structured Offer Extractor**: High-reasoning offer extraction using **Google Gemini 2.0 Flash** with automatic **OpenRouter** fallback.
- **🛡️ Smart Filtering & Validation**:
  - Enforces schema and required fields.
  - Geo-restriction prioritization (`global` > `europe` > `asia` > `us`) and US-only deal auto-flagging.
  - Recency window checking (90-day validity window).
  - Multi-level URL deduplication.
- **💾 SQLite Caching Engine**: Local SQLite storage (`offers.db`) preventing duplicate processing and tracking offer history.
- **🎨 Sleek Streamlit Dashboard**: Dark glassmorphism UI with live execution feed, metric counters, category & region filters, and CSV export.

---

## 🏗️ Core Architecture Flow

```
1. SEARCH (DDG / SearXNG) 
   └─► 2. FETCH (Jina Reader) 
        └─► 3. EXTRACT (Gemini 2.0 / OpenRouter) 
             └─► 4. FILTER (Validation / Geo / Recency) 
                  └─► 5. DISPLAY & CACHE (SQLite + Streamlit)
```

For complete technical specifications, see [`Kleros_Architecture.md`](file:///d:/Projects/Kleros/Kleros_Architecture.md).

---

## 🚀 Quick Start Guide

### 1. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/Hashimk101/Kleros.git
cd Kleros
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and set your API keys:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Primary LLM API Key (Required)
GEMINI_API_KEY=your_gemini_api_key_here

# Fallback LLM API Key (Required)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional SearXNG instances
SEARX_1=https://searx.tiekoetter.com/
SEARX_2=https://searx.rhscz.eu/
SEARX_3=https://search.rhscz.eu/
```

---

## 💻 Running the Application

### Launch Streamlit Interactive Dashboard

```bash
streamlit run dashboard.py
```

Open your browser at `http://localhost:8501` to use the interactive dashboard:
1. Enter your search query or use the pre-configured prompt.
2. Click **🚀 Run Agent** to trigger the discovery pipeline.
3. Track progress live in the execution feed.
4. Filter deals by type (`API`, `IDE`, `Chat`, `Student`) or region.
5. Export deal reports to CSV.

---

## 🧪 Running Automated Tests

Kleros includes a comprehensive test suite for all pipeline components:

```bash
python -m unittest discover tests
```

---

## 📁 Repository Structure

```
Kleros/
├── src/
│   ├── __init__.py
│   ├── database.py       # SQLite database initialization & CRUD queries
│   ├── search.py         # Multi-source search router (DuckDuckGo + SearXNG)
│   ├── fetch.py          # Async content fetcher via Jina Reader
│   ├── extractor.py      # Structured LLM offer extractor (Gemini + OpenRouter)
│   ├── filter.py         # Filtering & validation engine (Geo, Recency, Deduplication)
│   └── agent.py          # Main KlerosAgent pipeline orchestrator
├── tests/
│   ├── test_database.py  # SQLite DB unit tests
│   ├── test_search.py    # Search router unit tests
│   ├── test_fetch.py     # Content fetcher unit tests
│   ├── test_extractor.py # LLM extractor unit tests
│   ├── test_filter.py    # Filter engine unit tests
│   └── test_agent.py    # Orchestrator end-to-end tests
├── dashboard.py          # Interactive Streamlit dashboard
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
├── Kleros_Architecture.md # Project architecture blueprint
├── README.md             # Project documentation
└── LICENSE               # GNU General Public License v3.0
```

---

## 📄 License

Distributed under the **GNU General Public License v3.0**. See `LICENSE` for details.
