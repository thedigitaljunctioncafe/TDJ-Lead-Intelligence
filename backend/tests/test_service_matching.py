import unittest

from app.service_matching import match_services


def get_service_codes(text):
    return {
        item["service_code"]
        for item in match_services(text)
    }


class TestWebsiteMatching(unittest.TestCase):

    # Positive English and Bengali intent

    def test_english_website_requirement(self):
        self.assertIn("WEBSITE", get_service_codes(
            "I need a website"
        ))

    def test_bengali_website_requirement(self):
        self.assertIn("WEBSITE", get_service_codes(
            "আমার ওয়েবসাইট দরকার"
        ))

    def test_bengali_website_creation_requirement(self):
        self.assertIn("WEBSITE", get_service_codes(
            "আমার একটি ওয়েবসাইট তৈরি করা দরকার"
        ))

    def test_bengali_website_development_intent(self):
        self.assertIn("WEBSITE", get_service_codes(
            "আমি ওয়েবসাইট বানাতে চাই"
        ))

    # Negative intent

    def test_english_negative_intent(self):
        self.assertNotIn("WEBSITE", get_service_codes(
            "I do not need a website"
        ))

    def test_bengali_negative_need(self):
        self.assertNotIn("WEBSITE", get_service_codes(
            "আমার ওয়েবসাইট লাগবে না"
        ))

    def test_bengali_negative_creation(self):
        self.assertNotIn("WEBSITE", get_service_codes(
            "আমার ওয়েবসাইট তৈরি করা দরকার নেই"
        ))

    def test_bengali_negative_want(self):
        self.assertNotIn("WEBSITE", get_service_codes(
            "আমি ওয়েবসাইট বানাতে চাই না"
        ))

    # Generic mentions must not become leads

    def test_existing_website(self):
        self.assertNotIn("WEBSITE", get_service_codes(
            "আমার একটি ওয়েবসাইট আছে"
        ))

    def test_website_seen(self):
        self.assertNotIn("WEBSITE", get_service_codes(
            "আমি একটি ওয়েবসাইট দেখেছি"
        ))

    def test_generic_website_description(self):
        self.assertNotIn("WEBSITE", get_service_codes(
            "ওয়েবসাইটটি খুব সুন্দর"
        ))

    # Developer category separation

    def test_website_developer_not_real_estate(self):
        codes = get_service_codes(
            "Looking for a website developer"
        )

        self.assertIn("WEBSITE", codes)
        self.assertNotIn("MUTATION", codes)
        self.assertNotIn("PORCHA", codes)
        self.assertNotIn("KHAJNA", codes)

    def test_real_estate_developer(self):
        codes = get_service_codes(
            "A real estate developer is launching a new project"
        )

        self.assertIn("MUTATION", codes)
        self.assertIn("PORCHA", codes)
        self.assertIn("KHAJNA", codes)

    # Empty input

    def test_empty_input(self):
        self.assertEqual(match_services(""), [])

    def test_invalid_input(self):
        self.assertEqual(match_services(None), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
