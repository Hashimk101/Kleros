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

            # Deduplication check
            url = processed["url"].strip().rstrip("/")
            if url in seen_urls:
                continue
            seen_urls.add(url)

            processed["is_valid"] = True
            filtered.append(processed)

        logger.info(f"Filter Engine passed {len(filtered)} / {len(raw_offers)} valid offers.")
        return filtered
