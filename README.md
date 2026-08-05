# Kleros - Autonomous Discovery Agent

Kleros is an autonomous agent pipeline designed to discover, extract, and verify free AI resources. This includes LLM API credits, IDE subscriptions, chat plans, and general student deals. It leverages search engines, direct fetching via Jina Reader, and Large Language Models (LLMs) to automatically construct a verified database of active deals.

## Architecture

The system executes a 5-step pipeline:

1. Search: Queries DuckDuckGo and SearXNG for relevant deals. For the "All" category, the system runs simultaneous dual-searches for APIs and IDEs, interleaving results so each discovery run surfaces a balanced mix of both types.
2. Fetch: Uses Jina Reader (with fallback direct HTTP requests) to retrieve clean Markdown content from discovered web pages.
3. Extract: Uses Gemini Flash (with OpenRouter free models as a fallback) to extract structured JSON data about each deal, capturing the provider name, pricing details, daily limits, eligibility requirements, and geographic restrictions.
4. Filter: A local Python rule engine validates extracted offers against schema requirements, recency checks, geo-restriction flags, and an aggressive regex pattern for paid pricing language. The paid-deal filter is intentionally scoped only to API and Chat categories to preserve legitimate student deals that reference retail prices in their "normally X, free for students" phrasing.
5. Store: Saves valid, deduplicated offers to a local SQLite database (offers.db).

The system includes an editorial dark-theme dashboard built with Streamlit for reviewing, filtering, and exporting the discovered deals.

## Dashboard Overview

### Navigation Tabs

The dashboard is divided into three tabs:

- Live Feed: The main deal browser. Shows all discovered deals with search, sort, and filter controls.
- Analytics: Bar charts and visual breakdowns of the deal database by category and region.
- Pipeline Log: A scrollable chronological log of all pipeline runs, their status, and discovered offer counts.

### Metric Cards

Six metric cards at the top of the Live Feed tab summarize the current database state:

- Total Deals: The total number of verified offers in the database.
- New Today: Deals discovered within the current calendar day.
- API Credits: Count of offers classified as LLM API free-tier or credit grants.
- IDE Credits: Count of free IDE subscriptions (e.g., Cursor, Zed, JetBrains).
- Chat Plans: Count of free chat-interface plans (e.g., Claude, ChatGPT, Gemini).
- Success Rate: The percentage of pipeline runs that returned at least one valid deal.

### Deal Card Indicators

Each deal card displays several visual indicators to help you quickly assess the quality and freshness of an offer:

#### Freshness Dot

A colored dot in the top-right corner of each card indicates how recently the deal was discovered or last confirmed:

- Green dot: Posted or confirmed within the last 7 days. Likely still active.
- Yellow dot: Posted between 8 and 30 days ago. May still be active but worth verifying.
- Red dot: Posted more than 30 days ago. Treat with caution; the offer may have expired.

#### Verification Badge

A badge on the card indicates the trustworthiness of the source URL:

- OFFICIAL: The deal URL belongs to a first-party domain of a known AI provider (e.g., openai.com, anthropic.com, google.com, github.com, nvidia.com, zed.dev, groq.com, mistral.ai, cloudflare.com). These deals come directly from the provider and are considered highly reliable.
- SOURCE: The deal was found on an aggregator, blog, documentation mirror, or other third-party site. The deal may be legitimate but should be verified at the provider's own site before relying on it.

#### Category Tags

Each card carries a type tag identifying the category of the deal:

- API: A free-tier or credit-grant offer for programmatic LLM API access.
- IDE: A free subscription to an AI-powered development environment (e.g., Cursor Pro, Zed, JetBrains AI).
- Chat: A free plan for a consumer-facing AI chat interface.
- Student: A deal specifically gated by student or academic institution status.

#### Region Tag

Cards also display a geographic availability tag:

- Global: The offer is available to users worldwide with no known country restrictions.
- US Only / EU Only / etc.: The offer is geographically restricted. Eligibility may vary.

### Live Pipeline Status and Control

When triggering "Discover Free Deals", the UI displays real-time operational feedback:

- Progress Bar: Visual status bar reflecting step progress from 0% to 100%.
- Terminal Log Output: Real-time terminal output box displaying execution steps (e.g., `[$] STEP [SEARCH] - Running dual-search for APIs and IDEs...`).
- Pipeline Cancellation: A dedicated "Cancel Pipeline" button allowing operators to cleanly interrupt and terminate active discovery runs at any point without corrupting database integrity.

### Filters and Search

- Inline Search: The search bar filters deals in real time by name, provider, or keyword.
- Sort By: Sort the deal list by newest first or alphabetically by name.
- Filter Category: Narrow the list to a specific deal type (API, IDE, Chat, Student, or All).
- Filter Region: Narrow the list to a specific geographic availability.
- Quick Filters: Three one-click checkboxes for common views:
  - Global Only: Shows only deals with no geographic restrictions.
  - Added Today: Shows only deals discovered in the current calendar day.
  - High Value: Shows deals that offer particularly high credit amounts or long subscription durations.

## Automated Scheduled Collection (GitHub Actions)

Kleros supports automated, hands-free background collection via GitHub Actions workflows (`collector.yml`):

- Scheduled Execution: Runs automatically on a periodic cron schedule to continuously search, extract, filter, and store new AI deals without manual intervention.
- Manual Workflow Dispatch: Supports on-demand execution via GitHub's `workflow_dispatch` trigger directly from the Actions tab.
- Database Synchronization: Automatically commits and persists freshly discovered deals to the repository database, maintaining a constantly updated resource hub.

## Prerequisites

- Python 3.10 or higher
- Git

## Setup Instructions

1. Clone the repository:

       git clone https://github.com/Hashimk101/Kleros.git
       cd Kleros

2. Create a virtual environment and activate it:

       python -m venv venv

   On Windows:

       venv\Scripts\activate

   On macOS/Linux:

       source venv/bin/activate

3. Install the required dependencies:

       pip install -r requirements.txt

4. Set up environment variables by copying the example file and editing it with your API keys:

       cp .env.example .env

## API Configuration

Configure the following keys in your .env file before running the pipeline:

- GEMINI_API_KEY: Required. Used for the primary LLM extraction step. A free-tier key is available from Google AI Studio (aistudio.google.com).
- OPENROUTER_API_KEY: Required. Used as a fallback extractor when Gemini is rate-limited. OpenRouter provides free access to open-weights models including Gemma and Llama variants. A free account is available at openrouter.ai.
- JINA_API_KEY: Optional but recommended. Jina Reader converts web pages to clean Markdown for higher-quality extraction. If not provided, the system falls back to direct HTTP requests. A free key is available at jina.ai.

## Running the Dashboard

Launch the Streamlit dashboard with:

    streamlit run dashboard.py

The dashboard will open at http://localhost:8501. From the interface you can trigger the discovery pipeline, filter and search the deal database, and export verified deals as a CSV file.

## Running Unit Tests

The project includes a unit test suite covering the pipeline components including database storage, search routing, content fetching, and filter logic.

Run the full suite from the project root:

    python -m unittest discover tests

The test runner will automatically discover and execute all tests in the tests/ directory and report pass/fail status for each component.

## Project Structure

    Kleros/
    |-- dashboard.py          Main Streamlit dashboard application
    |-- src/
    |   |-- agent.py          Orchestrates the 5-step discovery pipeline
    |   |-- search.py         Search router (DuckDuckGo + SearXNG fallback)
    |   |-- fetch.py          Content fetcher (Jina Reader + direct HTTP fallback)
    |   |-- extract.py        LLM extraction layer (Gemini + OpenRouter fallback)
    |   |-- filter.py         Local rule-based validation and deduplication engine
    |   |-- database.py       SQLite storage interface
    |-- tests/
    |   |-- test_agent.py     End-to-end pipeline integration test
    |   |-- test_database.py  Database CRUD and stats tests
    |   |-- test_fetch.py     Content fetcher tests
    |   |-- test_filter.py    Filter engine validation tests
    |   |-- test_search.py    Search router and fallback tests
    |-- requirements.txt      Python dependency list
    |-- .env.example          Template for required environment variables
    |-- offers.db             SQLite database (auto-created on first run)
