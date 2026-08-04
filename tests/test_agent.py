import os
import unittest
from unittest.mock import MagicMock, patch
from src.agent import KlerosAgent


class TestKlerosAgent(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_agent_offers.db"
        if os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except PermissionError:
                pass
        self.agent = KlerosAgent(db_path=self.test_db, search_delay=0, fetch_delay=0, llm_delay=0)

    def tearDown(self):
        del self.agent
        import gc
        gc.collect()
        if os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except PermissionError:
                pass

    @patch("src.search.SearchRouter.search")
    @patch("src.fetch.ContentFetcher.fetch_all")
    @patch("src.extractor.LLMExtractor.extract_all")
    def test_pipeline_execution(self, mock_extract, mock_fetch, mock_search):
        mock_search.return_value = [
            {"url": "https://zed.dev/pricing", "title": "Zed", "snippet": "Zed IDE pricing"}
        ]
        mock_fetch.return_value = [
            {"url": "https://zed.dev/pricing", "markdown_content": "# Zed IDE Student Offer"}
        ]
        mock_extract.return_value = [
            {
                "name": "Zed IDE Student Plan",
                "url": "https://zed.dev/pricing",
                "offer_type": "ide",
                "value": "Free credits",
                "eligible_regions": ["global"]
            }
        ]

        progress_calls = []

        def callback(step, msg, pct):
            progress_calls.append((step, pct))

        result = self.agent.run(custom_query="test query", max_results=5, progress_callback=callback)

        self.assertEqual(result["valid_offers_count"], 1)
        self.assertEqual(result["new_offers_count"], 1)
        self.assertTrue(len(progress_calls) >= 5)


if __name__ == "__main__":
    unittest.main()
