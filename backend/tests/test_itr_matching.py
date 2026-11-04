import unittest

from app.service_matching import match_services


def get_service_codes(text):
    return {
        item["service_code"]
        for item in match_services(text)
    }


class TestITRMatching(unittest.TestCase):

    # English positive intent

    def test_need_itr(self):
        self.assertIn("ITR", get_service_codes(
            "I need ITR"
        ))

    def test_income_tax_return_requirement(self):
        self.assertIn("ITR", get_service_codes(
            "I need income tax return filing"
        ))

    def test_itr_filing(self):
        self.assertIn("ITR", get_service_codes(
            "I need ITR filing"
        ))

    # Bengali positive intent

    def test_bengali_itr_want(self):
        self.assertIn("ITR", get_service_codes(
            "আমি আইটিআর চাই"
        ))

    def test_bengali_income_tax_return(self):
        self.assertIn("ITR", get_service_codes(
            "আমার ইনকাম ট্যাক্স রিটার্ন ফাইলিং করতে হবে"
        ))

    # Negative intent

    def test_english_negative_itr(self):
        self.assertNotIn("ITR", get_service_codes(
            "I do not need ITR filing"
        ))

    def test_bengali_negative_itr_want(self):
        self.assertNotIn("ITR", get_service_codes(
            "আমি আইটিআর চাই না"
        ))

    def test_bengali_negative_itr_filing(self):
        self.assertNotIn("ITR", get_service_codes(
            "আমার আইটিআর ফাইলিং দরকার নেই"
        ))

    # Generic mention filtering

    def test_generic_income_tax_information(self):
        self.assertNotIn("ITR", get_service_codes(
            "Income tax return is an annual tax document"
        ))

    def test_generic_tax_information(self):
        self.assertNotIn("ITR", get_service_codes(
            "Tax compliance is important for every business"
        ))


if __name__ == "__main__":
    unittest.main(verbosity=2)
