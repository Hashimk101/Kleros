"""
Search Router module for discovering URLs from DuckDuckGo and SearXNG fallback instances.
"""

import os
import time
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import httpx
from ddgs import DDGS
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchRouter:
    """Discovers free resource URLs using DuckDuckGo with SearXNG fallback."""

    def __init__(
        self,
        searx_instances: Optional[List[str]] = None,
        search_delay: float = 1.0
    ):
        self.search_delay = search_delay
        if searx_instances:
            self.searx_instances = searx_instances
        else:
            self.searx_instances = [
                os.getenv("SEARX_1", "https://searx.tiekoetter.com/"),
                os.getenv("SEARX_2", "https://searx.rhscz.eu/"),
                os.getenv("SEARX_3", "https://search.rhscz.eu/")
            ]

    def _normalize_url(self, url: str) -> str:
        """Strip trailing slash and whitespace from URL."""
        if not url:
            return ""
        url = url.strip()
        parsed = urlparse(url)
        scheme = parsed.scheme.lower() if parsed.scheme else "https"
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip("/")
        normalized = f"{scheme}://{netloc}{path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized

    def search_duckduckgo(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search DuckDuckGo using the ddgs package."""
        results: List[Dict[str, Any]] = []
        try:
            logger.info(f"Searching DuckDuckGo for: '{query}'")
            ddgs = DDGS()
            ddg_results = list(ddgs.text(query, max_results=max_results))
            for item in ddg_results:
                href = item.get("href")
                if href:
                    results.append({
                        "url": self._normalize_url(href),
                        "title": item.get("title", ""),
                        "snippet": item.get("body", ""),
                        "source": "duckduckgo",
                        "date": item.get("date")
                    })
        except Exception as e:
            logger.warning(f"DuckDuckGo search error: {e}")
        return results

    def search_searxng(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search SearXNG public instances as fallback."""
        results: List[Dict[str, Any]] = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        for instance in self.searx_instances:
            base_url = instance.rstrip("/")
            endpoint = f"{base_url}/search"
            params = {
                "q": query,
                "format": "json",
                "language": "en"
            }
            try:
                logger.info(f"Querying SearXNG instance: {base_url}")
                response = httpx.get(endpoint, params=params, headers=headers, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    raw_results = data.get("results", [])
                    for item in raw_results[:max_results]:
                        url = item.get("url")
                        if url:
                            results.append({
                                "url": self._normalize_url(url),
                                "title": item.get("title", ""),
                                "snippet": item.get("content", ""),
                                "source": f"searxng ({base_url})",
                                "date": item.get("publishedDate")
                            })
                    if results:
                        logger.info(f"SearXNG instance {base_url} returned {len(results)} results.")
                        break
                else:
                    logger.warning(f"SearXNG instance {base_url} returned status {response.status_code}")
            except Exception as e:
                logger.warning(f"SearXNG instance {base_url} failed: {e}")
                continue

        return results

    def search(
        self,
        query: str,
        max_results: int = 10,
        min_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Main entry point for Search Router.
        1. Try DuckDuckGo first.
        2. If results < min_results, trigger SearXNG fallback.
        3. Deduplicate results by URL.
        """
        results = self.search_duckduckgo(query, max_results=max_results)
        time.sleep(self.search_delay)

        if len(results) < min_results:
            logger.info(f"DuckDuckGo returned only {len(results)} results. Triggering SearXNG fallback...")
            searx_results = self.search_searxng(query, max_results=max_results)
            results.extend(searx_results)

        # Deduplicate by URL preserving order
        unique_results: List[Dict[str, Any]] = []
        seen_urls = set()

        for item in results:
            url = item["url"]
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(item)

        logger.info(f"Search Router found total {len(unique_results)} unique results.")
        return unique_results[:max_results]
