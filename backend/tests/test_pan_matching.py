import unittest

from app.service_matching import match_services


def get_service_codes(text):
    return {
        item["service_code"]
        for item in match_services(text)
    }


class TestPANMatching(unittest.TestCase):

    # English positive intent

    def test_need_pan_card(self):
        self.assertIn("PAN", get_service_codes(
            "I need pan card"
        ))

    def test_pan_card_apply(self):
        self.assertIn("PAN", get_service_codes(
            "I want pan card apply"
        ))

    def test_pan_application(self):
        self.assertIn("PAN", get_service_codes(
            "I need pan application"
        ))

    # Bengali positive intent

    def test_bengali_pan_card_want(self):
        self.assertIn("PAN", get_service_codes(
            "আমি প্যান কার্ড চাই"
        ))

    def test_bengali_pan_card_apply(self):
        self.assertIn("PAN", get_service_codes(
            "আমি প্যান কার্ড করতে চাই"
        ))

    # Negative intent

    def test_english_negative_pan_intent(self):
        self.assertNotIn("PAN", get_service_codes(
            "I do not need pan card"
        ))

    def test_bengali_negative_pan_want(self):
        self.assertNotIn("PAN", get_service_codes(
            "আমি প্যান কার্ড চাই না"
        ))

    def test_bengali_negative_pan_apply(self):
        self.assertNotIn("PAN", get_service_codes(
            "আমি প্যান কার্ড করতে চাই না"
        ))

    # Generic mention filtering

    def test_existing_pan_card(self):
        self.assertNotIn("PAN", get_service_codes(
            "আমার একটি প্যান কার্ড আছে"
        ))

    def test_generic_pan_card_mention(self):
        self.assertNotIn("PAN", get_service_codes(
            "PAN card is an important identity document"
        ))


if __name__ == "__main__":
    unittest.main(verbosity=2)
