"""
Content Fetcher module using Jina Reader API to extract clean Markdown from web pages.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}


class ContentFetcher:
    """Fetches clean Markdown content using Jina Reader API (https://r.jina.ai/)."""

    def __init__(
        self,
        jina_prefix: str = "https://r.jina.ai/",
        timeout: float = 15.0,
        fetch_delay: float = 0.5
    ):
        self.jina_prefix = jina_prefix
        self.timeout = timeout
        self.fetch_delay = fetch_delay

    async def fetch_url_async(self, client: httpx.AsyncClient, target_url: str) -> Optional[str]:
        """Fetch clean Markdown content for a single URL asynchronously using Jina Reader."""
        jina_url = f"{self.jina_prefix.rstrip('/')}/{target_url}"
        try:
            logger.info(f"Fetching content via Jina Reader: {target_url}")
            response = await client.get(jina_url, headers=DEFAULT_HEADERS, timeout=self.timeout)
            if response.status_code == 200 and response.text.strip():
                return response.text
            else:
                logger.warning(f"Jina Reader returned status {response.status_code} for {target_url}")
                return None
        except Exception as e:
            logger.warning(f"Failed to fetch content for {target_url} via Jina Reader: {e}")
            return None

    async def fetch_all_async(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fetch content for a list of search results in parallel.
        Returns search results enriched with a 'markdown_content' field.
        """
        fetched_results: List[Dict[str, Any]] = []
        async with httpx.AsyncClient(follow_redirects=True) as client:
            tasks = []
            for item in search_results:
                url = item.get("url")
                if url:
                    tasks.append(self.fetch_url_async(client, url))
                else:
                    tasks.append(asyncio.sleep(0, result=None))

            contents = await asyncio.gather(*tasks, return_exceptions=True)

            for item, content in zip(search_results, contents):
                item_copy = dict(item)
                if isinstance(content, str) and content.strip():
                    item_copy["markdown_content"] = content
                    fetched_results.append(item_copy)
                else:
                    logger.warning(f"Skipping {item.get('url')} due to missing or failed content.")

        return fetched_results

    def fetch_all(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Synchronous wrapper for fetch_all_async."""
        if not search_results:
            return []
        try:
            return asyncio.run(self.fetch_all_async(search_results))
        except RuntimeError:
            # Fallback if an event loop is already running (e.g., in Jupyter/Streamlit)
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.fetch_all_async(search_results))
