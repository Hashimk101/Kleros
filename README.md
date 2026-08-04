# Kleros - Autonomous Discovery Agent

Kleros is an autonomous agent pipeline designed to discover, extract, and verify free AI resources. This includes LLM API credits, IDE subscriptions, chat plans, and general student deals. It leverages search engines, direct fetching via Jina Reader, and Large Language Models (LLMs) to automatically construct a verified database of active deals.

## Architecture

The system executes a 5-step pipeline:
1. Search: Queries DuckDuckGo and SearXNG for relevant deals, automatically interleaving results for APIs and IDEs.
2. Fetch: Uses Jina Reader and fallback direct HTTP requests to retrieve clean markdown from discovered web pages.
3. Extract: Uses Gemini Flash (with OpenRouter free models as a fallback) to extract structured JSON data about the deals, strictly capturing the provider names and daily limits.
4. Filter: A local Python engine filters out outdated deals and rejects paid options based on aggressive regex patterns.
5. Store: Saves valid offers to a local SQLite database (offers.db).

The system includes a Swiss Minimalist dashboard built with Streamlit for reviewing and exporting the discovered deals.

## Prerequisites

- Python 3.10 or higher
- Git

## Setup Instructions

1. Clone the repository:
   git clone https://github.com/Hashimk101/Kleros.git
   cd Kleros

2. Create a virtual environment and activate it:
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate

3. Install the required dependencies:
   pip install -r requirements.txt

4. Set up environment variables:
   Copy the example environment file and configure it with your API keys.
   cp .env.example .env

## API Configuration

To run the pipeline, you need to configure the following API keys in your .env file:

- GEMINI_API_KEY: Required for the primary LLM extraction step. You can obtain a free tier key from Google AI Studio.
- OPENROUTER_API_KEY: Required for the fallback extraction step. OpenRouter provides access to free open-weights models (like Gemma and Llama) that the system uses if Gemini is rate-limited.
- JINA_API_KEY (Optional but recommended): Jina Reader is used to parse web pages into clean markdown. If not provided or if rate-limited, the system will fall back to direct HTTP requests.

## Running the Dashboard

To launch the Streamlit dashboard:

streamlit run dashboard.py

The dashboard will be available at http://localhost:8501. From the UI, you can trigger the autonomous discovery pipeline, filter results by category and region, and export verified deals as a CSV file.

## Running Unit Tests

The project includes a suite of unit tests to verify the pipeline components, including database storage, search routing, and filter logic.

To run the tests, execute the following command in the root directory:

python -m unittest discover tests

This will automatically discover and execute all tests located in the tests/ directory.
