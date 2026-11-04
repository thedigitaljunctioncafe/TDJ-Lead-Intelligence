import unittest

from app.service_matching import match_services


def get_service_codes(text):
    return {
        item["service_code"]
        for item in match_services(text)
    }


class TestRationMatching(unittest.TestCase):

    # English positive intent

    def test_need_ration_card(self):
        self.assertIn("RATION", get_service_codes(
            "I need a ration card"
        ))

    def test_apply_for_ration_card(self):
        self.assertIn("RATION", get_service_codes(
            "I want to apply for a ration card"
        ))

    # Bengali positive intent

    def test_bengali_ration_card_want(self):
        self.assertIn("RATION", get_service_codes(
            "\u0986\u09ae\u09bf \u09b0\u09c7\u09b6\u09a8 \u0995\u09be\u09b0\u09cd\u09a1 \u099a\u09be\u0987"
        ))

    def test_bengali_ration_card_apply(self):
        self.assertIn("RATION", get_service_codes(
            "\u0986\u09ae\u09bf \u09b0\u09c7\u09b6\u09a8 \u0995\u09be\u09b0\u09cd\u09a1 \u0995\u09b0\u09a4\u09c7 \u099a\u09be\u0987"
        ))

    # Negative intent

    def test_english_negative_ration(self):
        self.assertNotIn("RATION", get_service_codes(
            "I do not need a ration card"
        ))

    def test_bengali_negative_ration_want(self):
        self.assertNotIn("RATION", get_service_codes(
            "\u0986\u09ae\u09bf \u09b0\u09c7\u09b6\u09a8 \u0995\u09be\u09b0\u09cd\u09a1 \u099a\u09be\u0987 \u09a8\u09be"
        ))

    # Generic mention filtering

    def test_existing_ration_card(self):
        self.assertNotIn("RATION", get_service_codes(
            "\u0986\u09ae\u09be\u09b0 \u098f\u0995\u099f\u09bf \u09b0\u09c7\u09b6\u09a8 \u0995\u09be\u09b0\u09cd\u09a1 \u0986\u099b\u09c7"
        ))

    def test_generic_ration_card_information(self):
        self.assertNotIn("RATION", get_service_codes(
            "A ration card is used for food distribution"
        ))

    def test_ration_policy_news(self):
        self.assertNotIn("RATION", get_service_codes(
            "The government announced new ration card rules"
        ))

    def test_empty_input(self):
        self.assertNotIn("RATION", get_service_codes(""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
