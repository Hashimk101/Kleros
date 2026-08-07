"""
Content Fetcher module using Jina Reader API with direct httpx fallback.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

JINA_HEADERS = {
    "Accept": "text/plain",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

DIRECT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}


class ContentFetcher:
    """Fetches clean content using Jina Reader API with direct httpx fallback."""

    def __init__(
        self,
        jina_prefix: str = "https://r.jina.ai/",
        timeout: float = 15.0,
        fetch_delay: float = 0.5
    ):
        self.jina_prefix = jina_prefix
        self.timeout = timeout
        self.fetch_delay = fetch_delay

    async def resolve_canonical_url_async(self, client: httpx.AsyncClient, target_url: str) -> str:
        """Follow HTTP 301/302 redirects and return the final canonical destination URL."""
        if not target_url or not isinstance(target_url, str):
            return target_url
        try:
            resp = await client.head(target_url, headers=DIRECT_HEADERS, timeout=5.0, follow_redirects=True)
            return str(resp.url)
        except Exception:
            try:
                resp = await client.get(target_url, headers=DIRECT_HEADERS, timeout=5.0, follow_redirects=True)
                return str(resp.url)
            except Exception as e:
                logger.warning(f"Could not resolve canonical URL for {target_url}: {e}")
                return target_url

    def resolve_canonical_url(self, target_url: str) -> str:
        """Synchronous wrapper for resolve_canonical_url_async."""
        if not target_url or not isinstance(target_url, str):
            return target_url
        try:
            with httpx.Client(headers=DIRECT_HEADERS, timeout=5.0, follow_redirects=True) as client:
                resp = client.head(target_url)
                return str(resp.url)
        except Exception:
            try:
                with httpx.Client(headers=DIRECT_HEADERS, timeout=5.0, follow_redirects=True) as client:
                    resp = client.get(target_url)
                    return str(resp.url)
            except Exception:
                return target_url

    async def fetch_via_jina(self, client: httpx.AsyncClient, target_url: str) -> Optional[str]:
        """Fetch clean Markdown via Jina Reader."""
        jina_url = f"{self.jina_prefix.rstrip('/')}/{target_url}"
        try:
            response = await client.get(jina_url, headers=JINA_HEADERS, timeout=self.timeout)
            if response.status_code == 200 and response.text.strip():
                return response.text
            else:
                logger.warning(f"Jina returned {response.status_code} for {target_url}")
                return None
        except Exception as e:
            logger.warning(f"Jina failed for {target_url}: {e}")
            return None

    async def fetch_direct(self, client: httpx.AsyncClient, target_url: str) -> Optional[str]:
        """Fallback: fetch raw HTML directly and extract text."""
        try:
            response = await client.get(target_url, headers=DIRECT_HEADERS, timeout=self.timeout)
            if response.status_code == 200 and response.text.strip():
                text = response.text
                # Basic HTML tag stripping for LLM consumption
                import re
                text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()
                if len(text) > 200:  # Only keep if there's meaningful content
                    return text[:15000]
            return None
        except Exception as e:
            logger.warning(f"Direct fetch failed for {target_url}: {e}")
            return None

    async def fetch_url_async(self, client: httpx.AsyncClient, target_url: str) -> Optional[str]:
        """Try Jina first, fall back to direct fetch."""
        logger.info(f"Fetching content: {target_url}")
        content = await self.fetch_via_jina(client, target_url)
        if content:
            return content

        logger.info(f"Jina failed, trying direct fetch: {target_url}")
        content = await self.fetch_direct(client, target_url)
        return content

    async def fetch_all_async(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fetch content for all search results with Jina + direct fallback."""
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
                    logger.warning(f"Skipping {item.get('url')} - no content retrieved.")

        logger.info(f"ContentFetcher retrieved content for {len(fetched_results)}/{len(search_results)} URLs.")
        return fetched_results

    def fetch_all(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Synchronous wrapper for fetch_all_async."""
        if not search_results:
            return []
        try:
            return asyncio.run(self.fetch_all_async(search_results))
        except RuntimeError:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.fetch_all_async(search_results))
