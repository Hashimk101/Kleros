"""
Filter Engine module for validating, deduplicating, geo-flagging, and recency-checking offers.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VALID_OFFER_TYPES = {"api", "ide", "chat", "student"}


class FilterEngine:
    """Applies validation, geo-prioritization, recency, and deduplication rules."""

    def __init__(self, max_age_days: int = 90):
        self.max_age_days = max_age_days

    def _is_valid_url(self, url: str) -> bool:
        """Check if string is a valid HTTP/HTTPS URL."""
        if not url or not isinstance(url, str):
            return False
        parsed = urlparse(url.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)

    def validate_offer(self, offer: Dict[str, Any]) -> bool:
        """Validate required fields and offer structure."""
        if not isinstance(offer, dict):
            return False

        # 1. Required name check
        name = offer.get("name")
        if not name or not isinstance(name, str) or not name.strip():
            return False

        # 2. Required valid URL check
        url = offer.get("url")
        if not self._is_valid_url(url):
            return False

        # 3. Valid offer type check
        offer_type = offer.get("offer_type")
        if not offer_type or not isinstance(offer_type, str) or offer_type.lower() not in VALID_OFFER_TYPES:
            return False

        # 4. Strict Free Filter (Reject paid/cheap deals) - Only apply to API and Chat
        if offer_type.lower() in ("api", "chat"):
            import re
            value_desc = f"{offer.get('value', '')} {offer.get('description', '')}".lower()
            
            # Look for explicit pricing (e.g. $0.14, $1.50) or paid keywords
            paid_pattern = r"(\$[0-9]+\.[0-9]+)|(pay-as-you-go)|(cents per)|(price per)|(billed)"
            if re.search(paid_pattern, value_desc):
                logger.info(f"Filter Engine rejected PAID deal: {name}")
                return False

        # 5. Check for explicit deprecation or LLM invalid flag
        if offer.get("is_valid") is False:
            logger.info(f"Filter Engine rejected DEPRECATED/SUNSET deal (flagged by LLM): {name}")
            return False

        value_desc = f"{offer.get('value', '')} {offer.get('description', '')}".lower()
        sunset_keywords = ["deprecated", "no longer available", "sunset", "discontinued", "ended", "no longer active"]
        if any(kw in value_desc for kw in sunset_keywords):
            logger.info(f"Filter Engine rejected DEPRECATED deal (keyword match): {name}")
            return False

        return True

    def is_within_recency_window(self, date_str: Any) -> bool:
        """Return True if date_str is within last max_age_days or if date_str is missing."""
        if not date_str or not isinstance(date_str, str):
            return True

        try:
            posted_date = datetime.strptime(date_str.strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
            cutoff = datetime.now(timezone.utc) - timedelta(days=self.max_age_days)
            return posted_date >= cutoff
        except ValueError:
            # If date format invalid, keep offer to avoid missing valid deals
            return True

    def process_geo_flags(self, offer: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize eligible_regions and mark geo restriction flags."""
        processed = dict(offer)
        regions = processed.get("eligible_regions")

        if isinstance(regions, str):
            regions = [regions]
        elif not isinstance(regions, list):
            regions = ["global"]

        # Lowercase region strings
        norm_regions = [str(r).strip().lower() for r in regions if r]
        if not norm_regions:
            norm_regions = ["global"]

        processed["eligible_regions"] = norm_regions

        # Check if US/North America only
        us_only_set = {"us", "usa", "united states", "ca", "canada"}
        is_us_only = bool(norm_regions) and all(r in us_only_set for r in norm_regions)

        if is_us_only or processed.get("geo_restricted"):
            processed["geo_restricted"] = True
            if is_us_only:
                processed["us_only_flag"] = True
            else:
                processed["us_only_flag"] = False
        else:
            processed["geo_restricted"] = False
            processed["us_only_flag"] = False

        return processed

    def filter_search_results_before_fetch(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out search results that are explicitly outdated or marked expired
        BEFORE fetching and sending to the LLM.
        """
        fresh_results: List[Dict[str, Any]] = []
        outdated_years = {"2020", "2021", "2022", "2023", "2024"}
        current_year = datetime.now().year

        for item in search_results:
            title = (item.get("title") or "").lower()
            snippet = (item.get("snippet") or "").lower()
            url = (item.get("url") or "").lower()
            text_combined = f"{title} {snippet} {url}"

            # Skip if explicitly mentions expired deal status
            if any(term in text_combined for term in ["expired", "deal ended", "offer ended", "discontinued", "no longer available"]):
                logger.info(f"Pre-fetch filter rejected expired URL: {item.get('url')}")
                continue

            # Skip if it references old years (e.g. 2022, 2023) and does NOT mention current year
            has_old_year = any(yr in text_combined for yr in outdated_years)
            has_current_year = str(current_year) in text_combined or str(current_year - 1) in text_combined

            if has_old_year and not has_current_year:
                logger.info(f"Pre-fetch filter rejected outdated year URL: {item.get('url')}")
                continue

            fresh_results.append(item)

        logger.info(f"Pre-fetch filter retained {len(fresh_results)}/{len(search_results)} fresh search results.")
        return fresh_results

    def calculate_confidence_score(self, offer: Dict[str, Any]) -> int:
        """
        Calculate a composite Health/Confidence score (0 - 100%) for an offer:
        - Domain Trust (+35% for official first-party domains, +20% for third-party)
        - Schema & LLM Validated (+30%)
        - Value Detail Explicit (+15% if specific limits mentioned)
        - Recency (+20% for <7 days old, +10% for <30 days old)
        """
        score = 0
        url = (offer.get("url") or "").lower()

        # 1. Official domain check (+35% or +20%)
        official_domains = ["google", "openai", "nvidia", "zed.dev", "anthropic", "github", "mistral", "groq", "cloudflare", "cohere", "sambanova", "siliconflow", "vercel", "kilo.ai", "together.ai", "cerebras", "baseten"]
        if any(d in url for d in official_domains):
            score += 35
        else:
            score += 20

        # 2. LLM Validated & Active Schema (+30%)
        if offer.get("is_valid", True):
            score += 30

        # 3. Value Detail Specificity (+15%)
        val = (offer.get("value") or "").strip()
        if len(val) > 5 and val.lower() != "free credit / discount":
            score += 15
        else:
            score += 5

        # 4. Recency Window (+20% or +10%)
        date_posted = offer.get("date_posted")
        if date_posted:
            try:
                posted_dt = datetime.strptime(date_posted.strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
                days_old = (datetime.now(timezone.utc) - posted_dt).days
                if days_old <= 7:
                    score += 20
                elif days_old <= 30:
                    score += 10
                else:
                    score += 5
            except Exception:
                score += 15
        else:
            score += 15

        return min(100, max(0, score))

    def filter_offers(self, raw_offers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter and normalize raw extracted offers:
        1. Validate fields.
        2. Check recency window.
        3. Normalize geo-flags.
        4. Deduplicate by URL.
        """
        filtered: List[Dict[str, Any]] = []
        seen_urls = set()

        for offer in raw_offers:
            # Validate essential schema
            if not self.validate_offer(offer):
                logger.info(f"Offer rejected due to validation failure: {offer.get('name')}")
                continue

            # Recency check
            date_posted = offer.get("date_posted")
            if not self.is_within_recency_window(date_posted):
                logger.info(f"Offer rejected due to age > {self.max_age_days} days: {offer.get('name')}")
                continue

            # Geo processing
            processed = self.process_geo_flags(offer)

            # Preserve source_url
            if not processed.get("source_url"):
                processed["source_url"] = processed["url"]

            # Deduplication check
            url = processed["url"].strip().rstrip("/")
            if url in seen_urls:
                continue
            seen_urls.add(url)

            processed["is_valid"] = True
            processed["confidence_score"] = self.calculate_confidence_score(processed)
            filtered.append(processed)

        logger.info(f"Filter Engine passed {len(filtered)} / {len(raw_offers)} valid offers.")
        return filtered
