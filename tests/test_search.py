import unittest
from unittest.mock import MagicMock, patch
from src.search import SearchRouter


class TestSearchRouter(unittest.TestCase):
    def setUp(self):
        self.router = SearchRouter(search_delay=0.0)

    def test_normalize_url(self):
        url = "https://zed.dev/pricing/ "
        normalized = self.router._normalize_url(url)
        self.assertEqual(normalized, "https://zed.dev/pricing")

    @patch.object(SearchRouter, "search_duckduckgo")
    @patch.object(SearchRouter, "search_searxng")
    def test_search_primary_sufficient(self, mock_searx, mock_ddg):
        mock_ddg.return_value = [
            {"url": "https://a.com", "title": "A", "snippet": "A", "source": "duckduckgo"},
            {"url": "https://b.com", "title": "B", "snippet": "B", "source": "duckduckgo"},
            {"url": "https://c.com", "title": "C", "snippet": "C", "source": "duckduckgo"}
        ]
        results = self.router.search("test query", max_results=10, min_results=3)
        self.assertEqual(len(results), 3)
        mock_searx.assert_not_called()

    @patch.object(SearchRouter, "search_duckduckgo")
    @patch.object(SearchRouter, "search_searxng")
    def test_search_fallback_trigger(self, mock_searx, mock_ddg):
        mock_ddg.return_value = [
            {"url": "https://a.com", "title": "A", "snippet": "A", "source": "duckduckgo"}
        ]
        mock_searx.return_value = [
            {"url": "https://b.com", "title": "B", "snippet": "B", "source": "searxng"}
        ]
        results = self.router.search("test query", max_results=10, min_results=3)
        self.assertEqual(len(results), 2)
        mock_searx.assert_called_once()


if __name__ == "__main__":
    unittest.main()
