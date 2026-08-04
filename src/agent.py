"""
Kleros Agent Orchestrator linking Search, Fetch, Extract, Filter, and Database modules.
"""

import logging
import os
from typing import Any, Callable, Dict, List, Optional
from dotenv import load_dotenv

from src.database import DatabaseManager
from src.extractor import LLMExtractor
from src.fetch import ContentFetcher
from src.filter import FilterEngine
from src.search import SearchRouter

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CATEGORY_QUERIES = {
    "All": "free LLM API credits student IDE subscriptions ChatGPT Edu Gemini Flash 2026",
    "API": "free LLM API credits OpenRouter Gemini Flash Claude Groq student 2026",
    "IDE": "free IDE credits Zed Antigravity Cursor GitHub Copilot student 2026",
    "Chat": "free chat subscriptions ChatGPT Edu Gemini Student Claude Pro 2026",
    "Student": "student AI discounts free credits developer programs 2026"
}


def build_autonomous_query(category: str = "All") -> str:
    """Automatically synthesize search queries based on requested category."""
    cat_key = category.strip().capitalize() if category else "All"
    return CATEGORY_QUERIES.get(cat_key, CATEGORY_QUERIES["All"])


class KlerosAgent:
    """Main orchestrator running the 5-step autonomous discovery pipeline."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        max_age_days: int = 90,
        search_delay: float = 1.0,
        fetch_delay: float = 0.5,
        llm_delay: float = 2.0
    ):
        db_file = db_path or os.getenv("DB_PATH", "offers.db")
        self.db = DatabaseManager(db_file)
        self.search_router = SearchRouter(search_delay=search_delay)
        self.content_fetcher = ContentFetcher(fetch_delay=fetch_delay)
        self.llm_extractor = LLMExtractor(llm_delay=llm_delay)
        self.filter_engine = FilterEngine(max_age_days=max_age_days)

    def run(
        self,
        category: str = "All",
        custom_query: Optional[str] = None,
        max_results: int = 10,
        max_pages: int = 5,
        progress_callback: Optional[Callable[[str, str, float], None]] = None
    ) -> Dict[str, Any]:
        """
        Execute full autonomous discovery pipeline:
        1. SEARCH -> 2. FETCH -> 3. EXTRACT -> 4. FILTER -> 5. STORE
        Automatically constructs search query if custom_query is not explicitly set.
        """
        query = custom_query or build_autonomous_query(category)
        logger.info(f"Starting Kleros Agent pipeline for category '{category}' with query: '{query}'")

        def notify(step: str, msg: str, pct: float):
            if progress_callback:
                progress_callback(step, msg, pct)
            logger.info(f"[{step} - {int(pct * 100)}%] {msg}")

        # Step 1: SEARCH
        notify("Search", f"Autonomous search running for query: '{query}'", 0.1)
        search_results = self.search_router.search(query=query, max_results=max_results)
        notify("Search", f"Discovered {len(search_results)} search results.", 0.25)

        if not search_results:
            notify("Complete", "No search results discovered.", 1.0)
            return {"query": query, "raw_search_count": 0, "new_offers_count": 0, "offers": []}

        # Select top N pages to fetch
        pages_to_fetch = search_results[:max_pages]

        # Step 2: FETCH
        notify("Fetch", f"Fetching clean Markdown for top {len(pages_to_fetch)} URLs via Jina Reader...", 0.35)
        fetched_pages = self.content_fetcher.fetch_all(pages_to_fetch)
        notify("Fetch", f"Successfully fetched content for {len(fetched_pages)} pages.", 0.50)

        if not fetched_pages:
            notify("Complete", "Failed to retrieve content from search URLs.", 1.0)
            return {"query": query, "raw_search_count": len(search_results), "new_offers_count": 0, "offers": []}

        # Step 3: EXTRACT
        notify("Extract", "Extracting structured JSON offers using LLM (Gemini 2.0 Flash)...", 0.65)
        raw_offers = self.llm_extractor.extract_all(fetched_pages)
        notify("Extract", f"Extracted {len(raw_offers)} raw offer objects.", 0.75)

        # Step 4: FILTER
        notify("Filter", "Validating schema, recency, geo-restrictions, and deduplicating...", 0.85)
        valid_offers = self.filter_engine.filter_offers(raw_offers)
        notify("Filter", f"Filter engine retained {len(valid_offers)} valid offers.", 0.90)

        # Step 5: STORE
        notify("Store", "Saving valid offers to SQLite database...", 0.95)
        new_count = self.db.save_offers(valid_offers)
        notify("Store", f"Saved {len(valid_offers)} offers ({new_count} new) to database.", 1.0)

        return {
            "query": query,
            "category": category,
            "raw_search_count": len(search_results),
            "fetched_pages_count": len(fetched_pages),
            "raw_offers_count": len(raw_offers),
            "valid_offers_count": len(valid_offers),
            "new_offers_count": new_count,
            "offers": valid_offers
        }
