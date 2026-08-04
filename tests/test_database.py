import os
import unittest
from src.database import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_offers.db"
        if os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except PermissionError:
                pass
        self.db = DatabaseManager(self.test_db)

    def tearDown(self):
        del self.db
        import gc
        gc.collect()
        if os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except PermissionError:
                pass


    def test_save_and_retrieve_offer(self):
        offer = {
            "name": "Zed IDE Student Credit",
            "url": "https://zed.dev/pricing",
            "offer_type": "ide",
            "value": "Free Pro subscription for students",
            "description": "Student discount for Zed IDE",
            "geo_restricted": False,
            "eligible_regions": ["global"],
            "date_posted": "2026-08-01",
            "source_type": "official"
        }
        inserted = self.db.save_offer(offer)
        self.assertTrue(inserted)

        offers = self.db.get_offers(offer_type="ide")
        self.assertEqual(len(offers), 1)
        self.assertEqual(offers[0]["name"], "Zed IDE Student Credit")
        self.assertEqual(offers[0]["eligible_regions"], ["global"])

    def test_deduplication(self):
        offer = {
            "name": "Gemini API Free Tier",
            "url": "https://aistudio.google.com",
            "offer_type": "api",
            "value": "$300 credits"
        }
        self.assertTrue(self.db.save_offer(offer))
        self.assertFalse(self.db.save_offer(offer))
        stats = self.db.get_stats()
        self.assertEqual(stats["total_offers"], 1)


if __name__ == "__main__":
    unittest.main()
