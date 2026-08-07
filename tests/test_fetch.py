import unittest
from unittest.mock import AsyncMock, patch
import httpx
from src.fetch import ContentFetcher


class TestContentFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = ContentFetcher()

    @patch("httpx.AsyncClient.get")
    def test_fetch_all_async(self, mock_get):
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = "# Sample Deal Page\nGet $100 free credits for Zed IDE."
        mock_get.return_value = mock_response

        search_results = [
            {"url": "https://zed.dev/pricing", "title": "Zed Pricing", "snippet": "Pricing page"}
        ]
        results = self.fetcher.fetch_all(search_results)
        self.assertEqual(len(results), 1)
        self.assertIn("markdown_content", results[0])
        self.assertIn("$100 free credits", results[0]["markdown_content"])

    def test_resolve_canonical_url(self):
        url = "https://aistudio.google.com"
        resolved = self.fetcher.resolve_canonical_url(url)
        self.assertTrue(resolved.startswith("http"))


if __name__ == "__main__":
    unittest.main()
