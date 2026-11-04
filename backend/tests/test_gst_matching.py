import unittest

from app.service_matching import match_services


def get_service_codes(text):
    return {
        item["service_code"]
        for item in match_services(text)
    }


class TestGSTMatching(unittest.TestCase):

    # English positive intent

    def test_need_gst(self):
        self.assertIn("GST", get_service_codes(
            "I need GST"
        ))

    def test_gst_registration(self):
        self.assertIn("GST", get_service_codes(
            "I need GST registration"
        ))

    def test_gst_filing(self):
        self.assertIn("GST", get_service_codes(
            "I need GST filing"
        ))

    # Bengali positive intent

    def test_bengali_gst_want(self):
        self.assertIn("GST", get_service_codes(
            "আমি জিএসটি চাই"
        ))

    def test_bengali_gst_registration(self):
        self.assertIn("GST", get_service_codes(
            "আমার জিএসটি রেজিস্ট্রেশন দরকার"
        ))

    def test_bengali_gst_filing(self):
        self.assertIn("GST", get_service_codes(
            "আমার জিএসটি ফাইলিং করতে হবে"
        ))

    # Negative intent

    def test_english_negative_gst(self):
        self.assertNotIn("GST", get_service_codes(
            "I do not need GST registration"
        ))

    def test_bengali_negative_gst_want(self):
        self.assertNotIn("GST", get_service_codes(
            "আমি জিএসটি চাই না"
        ))

    def test_bengali_negative_gst_registration(self):
        self.assertNotIn("GST", get_service_codes(
            "আমার জিএসটি রেজিস্ট্রেশন দরকার নেই"
        ))

    # Generic mention filtering

    def test_generic_gst_information(self):
        self.assertNotIn("GST", get_service_codes(
            "GST is a tax system for businesses"
        ))


if __name__ == "__main__":
    unittest.main(verbosity=2)
