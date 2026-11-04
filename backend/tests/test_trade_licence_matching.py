import unittest

from app.service_matching import match_services


def get_service_codes(text):
    return {
        item["service_code"]
        for item in match_services(text)
    }


class TestTradeLicenceMatching(unittest.TestCase):

    # English positive intent

    def test_need_trade_licence(self):
        self.assertIn("TRADE_LICENSE", get_service_codes(
            "I need a trade licence"
        ))

    def test_apply_for_trade_licence(self):
        self.assertIn("TRADE_LICENSE", get_service_codes(
            "I want to apply for a trade licence"
        ))

    # Bengali positive intent

    def test_bengali_trade_licence_want(self):
        self.assertIn("TRADE_LICENSE", get_service_codes(
            "\u0986\u09ae\u09bf \u099f\u09cd\u09b0\u09c7\u09a1 \u09b2\u09be\u0987\u09b8\u09c7\u09a8\u09cd\u09b8 \u099a\u09be\u0987"
        ))

    def test_bengali_trade_licence_apply(self):
        self.assertIn("TRADE_LICENSE", get_service_codes(
            "\u0986\u09ae\u09bf \u099f\u09cd\u09b0\u09c7\u09a1 \u09b2\u09be\u0987\u09b8\u09c7\u09a8\u09cd\u09b8 \u0995\u09b0\u09a4\u09c7 \u099a\u09be\u0987"
        ))

    # Negative intent

    def test_english_negative_trade_licence(self):
        self.assertNotIn("TRADE_LICENSE", get_service_codes(
            "I do not need a trade licence"
        ))

    def test_bengali_negative_trade_licence(self):
        self.assertNotIn("TRADE_LICENSE", get_service_codes(
            "\u0986\u09ae\u09bf \u099f\u09cd\u09b0\u09c7\u09a1 \u09b2\u09be\u0987\u09b8\u09c7\u09a8\u09cd\u09b8 \u099a\u09be\u0987 \u09a8\u09be"
        ))

    # Generic mention filtering

    def test_existing_trade_licence(self):
        self.assertNotIn("TRADE_LICENSE", get_service_codes(
            "\u0986\u09ae\u09be\u09b0 \u098f\u0995\u099f\u09bf \u099f\u09cd\u09b0\u09c7\u09a1 \u09b2\u09be\u0987\u09b8\u09c7\u09a8\u09cd\u09b8 \u0986\u099b\u09c7"
        ))

    def test_generic_trade_licence_information(self):
        self.assertNotIn("TRADE_LICENSE", get_service_codes(
            "A trade licence is required for certain businesses"
        ))

    def test_trade_licence_policy_news(self):
        self.assertNotIn("TRADE_LICENSE", get_service_codes(
            "The municipality announced new trade licence rules"
        ))

    def test_empty_input(self):
        self.assertNotIn("TRADE_LICENSE", get_service_codes(""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
