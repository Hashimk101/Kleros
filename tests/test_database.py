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
    def test_cleanup_expired_offers(self):
        old_offer = {
            "name": "Expired API Deal",
            "url": "https://expired-api.example.com",
            "offer_type": "api",
            "value": "$50 credits",
            "date_posted": "2025-01-01"
        }
        recent_offer = {
            "name": "Fresh API Deal",
            "url": "https://fresh-api.example.com",
            "offer_type": "api",
            "value": "$100 credits",
            "date_posted": "2026-08-04"
        }
        self.db.save_offer(old_offer)
        self.db.save_offer(recent_offer)

        deleted = self.db.cleanup_expired_offers(days_limit=30)
        self.assertEqual(deleted, 1)

        offers = self.db.get_offers(offer_type="all")
        self.assertEqual(len(offers), 1)
        self.assertEqual(offers[0]["name"], "Fresh API Deal")


if __name__ == "__main__":
    unittest.main()
