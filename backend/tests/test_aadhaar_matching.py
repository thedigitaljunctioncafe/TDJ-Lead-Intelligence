import unittest

from app.service_matching import match_services


def get_service_codes(text):
    return {
        item["service_code"]
        for item in match_services(text)
    }


class TestAadhaarMatching(unittest.TestCase):

    # English positive intent

    def test_need_aadhaar_card(self):
        self.assertIn("AADHAAR", get_service_codes(
            "I need an Aadhaar card"
        ))

    def test_aadhaar_update(self):
        self.assertIn("AADHAAR", get_service_codes(
            "I need to update my Aadhaar card"
        ))

    # Bengali positive intent

    def test_bengali_aadhaar_want(self):
        self.assertIn("AADHAAR", get_service_codes(
            "\u0986\u09ae\u09bf \u0986\u09a7\u09be\u09b0 \u0995\u09be\u09b0\u09cd\u09a1 \u099a\u09be\u0987"
        ))

    def test_bengali_aadhaar_update(self):
        self.assertIn("AADHAAR", get_service_codes(
            "\u0986\u09ae\u09be\u09b0 \u0986\u09a7\u09be\u09b0 \u0995\u09be\u09b0\u09cd\u09a1 \u0986\u09aa\u09a1\u09c7\u099f \u0995\u09b0\u09be \u09a6\u09b0\u0995\u09be\u09b0"
        ))

    # Negative intent

    def test_english_negative_aadhaar(self):
        self.assertNotIn("AADHAAR", get_service_codes(
            "I do not need Aadhaar services"
        ))

    def test_bengali_negative_aadhaar_want(self):
        self.assertNotIn("AADHAAR", get_service_codes(
            "\u0986\u09ae\u09bf \u0986\u09a7\u09be\u09b0 \u099a\u09be\u0987 \u09a8\u09be"
        ))

    # Generic mention filtering

    def test_existing_aadhaar_card(self):
        self.assertNotIn("AADHAAR", get_service_codes(
            "\u0986\u09ae\u09be\u09b0 \u0986\u09a7\u09be\u09b0 \u0995\u09be\u09b0\u09cd\u09a1 \u0986\u099b\u09c7"
        ))

    def test_generic_aadhaar_information(self):
        self.assertNotIn("AADHAAR", get_service_codes(
            "Aadhaar is India's identity system"
        ))

    def test_aadhaar_news_mention(self):
        self.assertNotIn("AADHAAR", get_service_codes(
            "The government announced a new Aadhaar update facility"
        ))

    def test_empty_input(self):
        self.assertNotIn("AADHAAR", get_service_codes(""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
