import unittest

from app.service_matching import match_services


def get_service_codes(text):
    return {
        item["service_code"]
        for item in match_services(text)
    }


class TestVoterMatching(unittest.TestCase):

    # English positive intent

    def test_need_voter_id(self):
        self.assertIn("VOTER", get_service_codes(
            "I need a voter ID card"
        ))

    def test_apply_for_voter_card(self):
        self.assertIn("VOTER", get_service_codes(
            "I want to apply for a voter card"
        ))

    # Bengali positive intent

    def test_bengali_voter_card_want(self):
        self.assertIn("VOTER", get_service_codes(
            "\u0986\u09ae\u09bf \u09ad\u09cb\u099f\u09be\u09b0 \u0995\u09be\u09b0\u09cd\u09a1 \u099a\u09be\u0987"
        ))

    def test_bengali_voter_card_apply(self):
        self.assertIn("VOTER", get_service_codes(
            "\u0986\u09ae\u09bf \u09ad\u09cb\u099f\u09be\u09b0 \u0995\u09be\u09b0\u09cd\u09a1 \u0995\u09b0\u09a4\u09c7 \u099a\u09be\u0987"
        ))

    # Negative intent

    def test_english_negative_voter(self):
        self.assertNotIn("VOTER", get_service_codes(
            "I do not need a voter ID card"
        ))

    def test_bengali_negative_voter_want(self):
        self.assertNotIn("VOTER", get_service_codes(
            "\u0986\u09ae\u09bf \u09ad\u09cb\u099f\u09be\u09b0 \u0995\u09be\u09b0\u09cd\u09a1 \u099a\u09be\u0987 \u09a8\u09be"
        ))

    # Generic mention filtering

    def test_existing_voter_card(self):
        self.assertNotIn("VOTER", get_service_codes(
            "\u0986\u09ae\u09be\u09b0 \u098f\u0995\u099f\u09bf \u09ad\u09cb\u099f\u09be\u09b0 \u0995\u09be\u09b0\u09cd\u09a1 \u0986\u099b\u09c7"
        ))

    def test_generic_voter_id_information(self):
        self.assertNotIn("VOTER", get_service_codes(
            "A voter ID is an identity document"
        ))

    def test_voter_election_news(self):
        self.assertNotIn("VOTER", get_service_codes(
            "The election commission announced new voter ID rules"
        ))

    def test_empty_input(self):
        self.assertNotIn("VOTER", get_service_codes(""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
