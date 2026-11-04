import unittest

from app.service_matching import match_services


def get_service_codes(text):
    return {
        item["service_code"]
        for item in match_services(text)
    }


class TestLandRecordMatching(unittest.TestCase):

    # PORCHA

    def test_porcha_english_positive(self):
        self.assertIn("PORCHA", get_service_codes(
            "I need porcha"
        ))

    def test_porcha_bengali_positive(self):
        self.assertIn("PORCHA", get_service_codes(
            "আমি পর্চা চাই"
        ))

    def test_porcha_negative(self):
        self.assertNotIn("PORCHA", get_service_codes(
            "আমি পর্চা চাই না"
        ))

    def test_porcha_generic_mention(self):
        self.assertNotIn("PORCHA", get_service_codes(
            "পর্চা জমির রেকর্ডের একটি নথি"
        ))

    # MUTATION

    def test_mutation_english_positive(self):
        self.assertIn("MUTATION", get_service_codes(
            "I need land mutation"
        ))

    def test_mutation_bengali_positive(self):
        self.assertIn("MUTATION", get_service_codes(
            "আমি জমির মিউটেশন করতে চাই"
        ))

    def test_mutation_negative(self):
        self.assertNotIn("MUTATION", get_service_codes(
            "আমি জমির মিউটেশন করতে চাই না"
        ))

    def test_mutation_generic_mention(self):
        self.assertNotIn("MUTATION", get_service_codes(
            "Land mutation is a property record process"
        ))

    # KHAJNA

    def test_khajna_english_positive(self):
        self.assertIn("KHAJNA", get_service_codes(
            "I need khajna payment"
        ))

    def test_khajna_bengali_positive(self):
        self.assertIn("KHAJNA", get_service_codes(
            "আমি খাজনা দিতে চাই"
        ))

    def test_khajna_negative(self):
        self.assertNotIn("KHAJNA", get_service_codes(
            "আমি খাজনা দিতে চাই না"
        ))

    def test_khajna_generic_mention(self):
        self.assertNotIn("KHAJNA", get_service_codes(
            "Land revenue payment is required by land owners"
        ))

    # Service separation

    def test_porcha_does_not_match_mutation_or_khajna(self):
        codes = get_service_codes("আমি পর্চা চাই")
        self.assertIn("PORCHA", codes)
        self.assertNotIn("MUTATION", codes)
        self.assertNotIn("KHAJNA", codes)

    def test_mutation_does_not_match_porcha_or_khajna(self):
        codes = get_service_codes("আমি জমির মিউটেশন করতে চাই")
        self.assertIn("MUTATION", codes)
        self.assertNotIn("PORCHA", codes)
        self.assertNotIn("KHAJNA", codes)

    def test_khajna_does_not_match_porcha_or_mutation(self):
        codes = get_service_codes("আমি খাজনা দিতে চাই")
        self.assertIn("KHAJNA", codes)
        self.assertNotIn("PORCHA", codes)
        self.assertNotIn("MUTATION", codes)


if __name__ == "__main__":
    unittest.main(verbosity=2)
