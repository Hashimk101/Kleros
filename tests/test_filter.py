import unittest
from datetime import datetime, timedelta, timezone
from src.filter import FilterEngine


class TestFilterEngine(unittest.TestCase):
    def setUp(self):
        self.filter_engine = FilterEngine(max_age_days=90)

    def test_valid_offer(self):
        offer = {
            "name": "Zed IDE Pro Student",
            "url": "https://zed.dev/pricing",
            "offer_type": "ide",
            "eligible_regions": ["global"]
        }
        self.assertTrue(self.filter_engine.validate_offer(offer))

    def test_invalid_offer(self):
        # Missing URL
        offer = {"name": "No URL", "offer_type": "ide"}
        self.assertFalse(self.filter_engine.validate_offer(offer))

        # Invalid type
        offer_bad_type = {"name": "Test", "url": "https://test.com", "offer_type": "gpu"}
        self.assertFalse(self.filter_engine.validate_offer(offer_bad_type))

    def test_recency_window(self):
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        old_date_str = (datetime.now(timezone.utc) - timedelta(days=120)).strftime("%Y-%m-%d")

        self.assertTrue(self.filter_engine.is_within_recency_window(today_str))
        self.assertFalse(self.filter_engine.is_within_recency_window(old_date_str))

    def test_filter_and_deduplicate(self):
        raw_offers = [
            {
                "name": "Gemini API Free Tier",
                "url": "https://aistudio.google.com",
                "offer_type": "api",
                "eligible_regions": ["global"]
            },
            {
                "name": "Gemini API Duplicate",
                "url": "https://aistudio.google.com/",
                "offer_type": "api",
                "eligible_regions": ["global"]
            }
        ]
        filtered = self.filter_engine.filter_offers(raw_offers)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["name"], "Gemini API Free Tier")

    def test_source_url_preservation(self):
        raw_offers = [{
            "name": "Windsurf IDE",
            "url": "https://devin.ai/desktop",
            "source_url": "https://codeium.com/windsurf",
            "offer_type": "ide",
            "eligible_regions": ["global"]
        }]
        filtered = self.filter_engine.filter_offers(raw_offers)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["source_url"], "https://codeium.com/windsurf")


if __name__ == "__main__":
    unittest.main()
