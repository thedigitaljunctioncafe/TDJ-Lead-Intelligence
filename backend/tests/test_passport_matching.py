import unittest

from app.service_matching import match_services


def get_service_codes(text):
    return {
        item["service_code"]
        for item in match_services(text)
    }


class TestPassportMatching(unittest.TestCase):

    # English positive intent

    def test_need_passport(self):
        self.assertIn("PASSPORT", get_service_codes(
            "I need passport"
        ))

    def test_passport_apply(self):
        self.assertIn("PASSPORT", get_service_codes(
            "I want passport apply"
        ))

    def test_passport_application(self):
        self.assertIn("PASSPORT", get_service_codes(
            "I need passport application"
        ))

    # Bengali positive intent

    def test_bengali_passport_want(self):
        self.assertIn("PASSPORT", get_service_codes(
            "আমি পাসপোর্ট চাই"
        ))

    def test_bengali_passport_apply(self):
        self.assertIn("PASSPORT", get_service_codes(
            "আমি পাসপোর্ট করতে চাই"
        ))

    # Negative intent

    def test_english_negative_intent(self):
        self.assertNotIn("PASSPORT", get_service_codes(
            "I do not need passport"
        ))

    def test_bengali_negative_want(self):
        self.assertNotIn("PASSPORT", get_service_codes(
            "আমি পাসপোর্ট চাই না"
        ))

    def test_bengali_negative_apply(self):
        self.assertNotIn("PASSPORT", get_service_codes(
            "আমি পাসপোর্ট করতে চাই না"
        ))

    # Generic mention filtering

    def test_existing_passport(self):
        self.assertNotIn("PASSPORT", get_service_codes(
            "আমার একটি পাসপোর্ট আছে"
        ))

    def test_generic_passport_mention(self):
        self.assertNotIn("PASSPORT", get_service_codes(
            "A passport is an important travel document"
        ))


if __name__ == "__main__":
    unittest.main(verbosity=2)
