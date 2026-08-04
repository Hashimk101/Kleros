import unittest
from unittest.mock import MagicMock, patch
from src.extractor import LLMExtractor


class TestLLMExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = LLMExtractor(llm_delay=0.0)

    def test_clean_json_text(self):
        raw = "```json\n[{\"name\": \"Test Offer\"}]\n```"
        cleaned = self.extractor._clean_json_text(raw)
        self.assertEqual(cleaned, "[{\"name\": \"Test Offer\"}]")

    @patch.object(LLMExtractor, "extract_with_gemini")
    def test_extract_offers_from_page(self, mock_gemini):
        mock_gemini.return_value = [
            {
                "name": "Zed Student Plan",
                "url": "https://zed.dev/pricing",
                "offer_type": "ide",
                "value": "Free",
                "geo_restricted": False,
                "eligible_regions": ["global"]
            }
        ]

        offers = self.extractor.extract_offers_from_page("sample markdown content", "https://zed.dev/pricing")
        self.assertEqual(len(offers), 1)
        self.assertEqual(offers[0]["name"], "Zed Student Plan")


if __name__ == "__main__":
    unittest.main()
