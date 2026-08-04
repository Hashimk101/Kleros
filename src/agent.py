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
    "all": "free LLM API credits student IDE subscriptions 2026",
    "api": "free LLM API credits student",
    "ide": "free student IDE credits Zed Cursor",
    "chat": "free ChatGPT Edu Gemini Student subscription",
    "student": "free AI student deals developer credits"
}


def build_autonomous_query(category: str = "All") -> str:
    """Automatically synthesize search queries based on requested category."""
    cat_key = category.strip().lower() if category else "all"
    return CATEGORY_QUERIES.get(cat_key, CATEGORY_QUERIES["all"])


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
        """
        query = custom_query or build_autonomous_query(category)
        logger.info(f"Starting Kleros Agent pipeline for category '{category}' with query: '{query}'")

        def notify(step: str, msg: str, pct: float):
            if progress_callback:
                progress_callback(step, msg, pct)
            logger.info(f"[{step} - {int(pct * 100)}%] {msg}")

        # Default result structure to prevent KeyError
        result_payload = {
            "query": query,
            "category": category,
            "raw_search_count": 0,
            "fetched_pages_count": 0,
            "raw_offers_count": 0,
            "valid_offers_count": 0,
            "new_offers_count": 0,
            "offers": []
        }

        # Step 1: SEARCH
        notify("Search", f"Autonomous search running for query: '{query}'", 0.1)
        search_results = self.search_router.search(query=query, max_results=max_results)
        result_payload["raw_search_count"] = len(search_results)
        notify("Search", f"Discovered {len(search_results)} search results.", 0.25)

        if not search_results:
            notify("Complete", "No search results discovered.", 1.0)
            return result_payload

        # Filter out outdated or expired links BEFORE fetching to save LLM time & quota
        fresh_results = self.filter_engine.filter_search_results_before_fetch(search_results)
        if not fresh_results:
            notify("Complete", "All discovered links were identified as outdated or expired.", 1.0)
            return result_payload

        # Select top N pages to fetch
        pages_to_fetch = fresh_results[:max_pages]

        # Step 2: FETCH
        notify("Fetch", f"Fetching clean Markdown for top {len(pages_to_fetch)} URLs via Jina Reader...", 0.35)
        fetched_pages = self.content_fetcher.fetch_all(pages_to_fetch)
        result_payload["fetched_pages_count"] = len(fetched_pages)
        notify("Fetch", f"Successfully fetched content for {len(fetched_pages)} pages.", 0.50)

        if not fetched_pages:
            notify("Complete", "Failed to retrieve content from search URLs.", 1.0)
            return result_payload

        # Step 3: EXTRACT
        notify("Extract", "Extracting structured JSON offers using LLMs...", 0.60)
        
        # We define a custom callback for the extractor to report per-page progress
        def extract_progress(current: int, total: int, url: str):
            pct = 0.60 + (0.20 * (current / max(1, total)))
            notify("Extract", f"Extracting page {current}/{total}: {url}", pct)
            
        raw_offers = self.llm_extractor.extract_all(fetched_pages, progress_callback=extract_progress)
        result_payload["raw_offers_count"] = len(raw_offers)
        notify("Extract", f"Extracted {len(raw_offers)} raw offer objects.", 0.80)

        # Step 4: FILTER
        notify("Filter", "Validating schema, recency, geo-restrictions, and deduplicating...", 0.85)
        valid_offers = self.filter_engine.filter_offers(raw_offers)
        result_payload["valid_offers_count"] = len(valid_offers)
        result_payload["offers"] = valid_offers
        notify("Filter", f"Filter engine retained {len(valid_offers)} valid offers.", 0.90)

        # Step 5: STORE
        notify("Store", "Saving valid offers to SQLite database...", 0.95)
        new_count = self.db.save_offers(valid_offers)
        result_payload["new_offers_count"] = new_count
        notify("Store", f"Saved {len(valid_offers)} offers ({new_count} new) to database.", 1.0)

        return result_payload
