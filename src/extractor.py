"""
LLM Extractor module using Google Gemini with OpenRouter fallback for offer extraction.
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional
import httpx
from dotenv import load_dotenv
from google import genai

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert AI agent that finds free student AI resources. Extract structured offer data from the provided search result content.

Extract any offers matching these types:
- api: LLM API credits (OpenRouter, Gemini, Claude, Groq, SiliconFlow, SambaNova, etc.)
- ide: IDE credits/subscriptions (Zed, Antigravity, Cursor, GitHub Copilot, etc.)
- chat: Chat subscriptions (Gemini Student, ChatGPT Edu, Claude Pro, etc.)
- student: General student-specific AI programs & discounts

Return a JSON array of objects. Each object MUST include:
- name: (string) The specific PROVIDER or PLATFORM offering the free access (e.g., "SiliconFlow (DeepSeek)", "OpenRouter Free Tier", "Groq API", "SambaNova Cloud"). Do NOT just list the model name (like "DeepSeek")—you MUST include the platform hosting it for free.
- url: (string) Target URL for the offer
- offer_type: (string) Exactly one of "api", "ide", "chat", "student"
- value: (string) Exact details of the free tier (e.g., "Free daily quota", "Millions of free tokens/day", "$10 sign-up credit", "15 RPM free tier"). Be explicit about daily quotas.
- geo_restricted: (boolean) true if restricted to specific countries/regions, false if globally available
- eligible_regions: (array of strings) e.g., ["global"] or ["us", "europe", "asia"]
- date_posted: (string or null) "YYYY-MM-DD" format if mentioned, otherwise null
- source_type: (string) "official", "blog", "forum", or "social"
- description: (string) Brief summary of how to claim the offer and what limits apply (e.g., "Access DeepSeek and Qwen models with generous free daily quotas via their API").
- is_valid: (boolean) MUST be false if the page text indicates the offer is "deprecated", "no longer available", "sunset", "discontinued", or "ended". Otherwise true.

CRITICAL: Return ONLY a valid JSON array. Do not include markdown code block backticks or extra text outside the JSON.
"""

# OpenRouter free models to try in order of preference (prioritizing fast & reliable free models)
OPENROUTER_FREE_MODELS = [
    "google/gemma-4-26b-a4b-it:free",
    "inclusionai/ling-3.0-flash:free",
    "google/gemma-4-31b-it:free",
    "openai/gpt-oss-20b:free",
]


class LLMExtractor:
    """Extracts structured offers from web markdown using Gemini or OpenRouter."""

    def __init__(
        self,
        gemini_key: Optional[str] = None,
        openrouter_key: Optional[str] = None,
        llm_delay: float = 0.5
    ):
        self.gemini_key = gemini_key or os.getenv("GEMINI_API_KEY")
        self.openrouter_key = openrouter_key or os.getenv("OPENROUTER_API_KEY")
        self.llm_delay = llm_delay
        self._gemini_disabled = False

        self.gemini_client = None
        if self.gemini_key:
            try:
                self.gemini_client = genai.Client(api_key=self.gemini_key)
            except Exception as e:
                logger.warning(f"Could not initialize Gemini client: {e}")

    def _clean_json_text(self, text: str) -> str:
        """Strip markdown triple backticks and trim text."""
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()

    def extract_with_gemini(self, page_content: str, url: str) -> Optional[List[Dict[str, Any]]]:
        """Attempt Gemini ONCE. If it fails for ANY reason, immediately disable Gemini for all subsequent calls."""
        if not self.gemini_client or self._gemini_disabled:
            return None

        prompt = f"{SYSTEM_PROMPT}\n\nTarget URL: {url}\n\nPage Content:\n{page_content[:12000]}"

        try:
            logger.info(f"Extracting with Gemini 2.0 Flash (single attempt) for: {url}")
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            raw_text = response.text or ""
            cleaned = self._clean_json_text(raw_text)
            data = json.loads(cleaned)
            if isinstance(data, list):
                return data
        except Exception as e:
            logger.warning(f"Gemini attempt failed ({e}). Disabling Gemini for remaining requests; falling back to OpenRouter free models.")
            self._gemini_disabled = True
        return None

    def extract_with_openrouter(self, page_content: str, url: str) -> Optional[List[Dict[str, Any]]]:
        """Fallback extraction using OpenRouter free models."""
        if not self.openrouter_key:
            return None

        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json"
        }

        for model_id in OPENROUTER_FREE_MODELS:
            payload = {
                "model": model_id,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Target URL: {url}\n\nPage Content:\n{page_content[:12000]}"}
                ],
                "temperature": 0.2
            }

            try:
                logger.info(f"Trying OpenRouter model {model_id} for: {url}")
                response = httpx.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=15.0
                )
                if response.status_code == 200:
                    res_data = response.json()
                    content = res_data["choices"][0]["message"]["content"]
                    cleaned = self._clean_json_text(content)
                    data = json.loads(cleaned)
                    if isinstance(data, list):
                        logger.info(f"OpenRouter {model_id} extracted {len(data)} offers.")
                        return data
                else:
                    logger.warning(f"OpenRouter {model_id} returned HTTP {response.status_code}")
                    continue
            except Exception as e:
                logger.warning(f"OpenRouter {model_id} failed for {url}: {e}")
                continue

        return None

    def extract_offers_from_page(self, page_content: str, url: str) -> List[Dict[str, Any]]:
        """Attempt extraction via Gemini first (single try), fallback to OpenRouter free models."""
        if not page_content or not page_content.strip():
            return []

        # 1. Try Gemini (if not disabled)
        offers = self.extract_with_gemini(page_content, url)
        if offers is not None:
            return offers

        # 2. Fallback to OpenRouter
        logger.info(f"Using OpenRouter fallback for: {url}")
        offers = self.extract_with_openrouter(page_content, url)
        if offers is not None:
            return offers

        return []

    def extract_all(self, fetched_pages: List[Dict[str, Any]], progress_callback=None) -> List[Dict[str, Any]]:
        """Process multiple fetched pages sequentially with minimal delay."""
        all_extracted_offers: List[Dict[str, Any]] = []
        total_pages = len(fetched_pages)

        for idx, page in enumerate(fetched_pages):
            url = page.get("url", "")
            content = page.get("markdown_content", "")
            if not content:
                continue

            if progress_callback:
                progress_callback(idx + 1, total_pages, url)

            offers = self.extract_offers_from_page(content, url)
            for offer in offers:
                if isinstance(offer, dict):
                    if "url" not in offer or not offer["url"]:
                        offer["url"] = url
                    if "source_url" not in offer:
                        offer["source_url"] = url
                    all_extracted_offers.append(offer)

            time.sleep(self.llm_delay)

        logger.info(f"LLM Extractor discovered {len(all_extracted_offers)} raw offers.")
        return all_extracted_offers
