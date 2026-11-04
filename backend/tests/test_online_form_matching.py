import unittest

from app.service_matching import match_services


def get_service_codes(text):
    return {
        item["service_code"]
        for item in match_services(text)
    }


class TestOnlineFormMatching(unittest.TestCase):

    # English positive intent

    def test_need_online_form_filling(self):
        self.assertIn("ONLINE_FORM", get_service_codes(
            "I need help with online form filling"
        ))

    def test_want_form_filled(self):
        self.assertIn("ONLINE_FORM", get_service_codes(
            "I want someone to fill my online application form"
        ))

    # Bengali positive intent

    def test_bengali_online_form_help(self):
        self.assertIn("ONLINE_FORM", get_service_codes(
            "\u0986\u09ae\u09be\u09b0 \u0985\u09a8\u09b2\u09be\u0987\u09a8 \u09ab\u09b0\u09cd\u09ae \u09aa\u09c2\u09b0\u09a3 \u0995\u09b0\u09be \u09a6\u09b0\u0995\u09be\u09b0"
        ))

    def test_bengali_form_filling_want(self):
        self.assertIn("ONLINE_FORM", get_service_codes(
            "\u0986\u09ae\u09bf \u0985\u09a8\u09b2\u09be\u0987\u09a8 \u09ab\u09b0\u09cd\u09ae \u09ab\u09bf\u09b2\u0986\u09aa \u0995\u09b0\u09be\u09a4\u09c7 \u099a\u09be\u0987"
        ))

    # Negative intent

    def test_english_negative_online_form(self):
        self.assertNotIn("ONLINE_FORM", get_service_codes(
            "I do not need online form filling"
        ))

    def test_bengali_negative_online_form(self):
        self.assertNotIn("ONLINE_FORM", get_service_codes(
            "\u0986\u09ae\u09be\u09b0 \u0985\u09a8\u09b2\u09be\u0987\u09a8 \u09ab\u09b0\u09cd\u09ae \u09aa\u09c2\u09b0\u09a3 \u0995\u09b0\u09be \u09a6\u09b0\u0995\u09be\u09b0 \u09a8\u09c7\u0987"
        ))

    # Generic mention filtering

    def test_generic_online_form_information(self):
        self.assertNotIn("ONLINE_FORM", get_service_codes(
            "Online forms are used for government applications"
        ))

    def test_form_filling_tutorial(self):
        self.assertNotIn("ONLINE_FORM", get_service_codes(
            "This tutorial explains how online form filling works"
        ))

    def test_online_form_news(self):
        self.assertNotIn("ONLINE_FORM", get_service_codes(
            "The government launched a new online application form"
        ))

    def test_empty_input(self):
        self.assertNotIn("ONLINE_FORM", get_service_codes(""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
