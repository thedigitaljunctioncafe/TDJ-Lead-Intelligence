import unittest

from app.service_matching import match_services


def get_service_codes(text):
    return {item["service_code"] for item in match_services(text)}


class TestPrintScanMatching(unittest.TestCase):

    def test_need_printing_service(self):
        self.assertIn("PRINT_SCAN", get_service_codes("I need document printing service"))

    def test_need_scanning_service(self):
        self.assertIn("PRINT_SCAN", get_service_codes("I need someone to scan my documents"))

    def test_bengali_printing_service(self):
        self.assertIn("PRINT_SCAN", get_service_codes("আমার কিছু ডকুমেন্ট প্রিন্ট করতে হবে"))

    def test_bengali_print_and_scan_service(self):
        self.assertIn("PRINT_SCAN", get_service_codes("আমার ডকুমেন্ট স্ক্যান ও প্রিন্ট করে দিতে হবে"))

    def test_english_negative_printing(self):
        self.assertNotIn("PRINT_SCAN", get_service_codes("I do not need printing service"))

    def test_bengali_negative_printing(self):
        self.assertNotIn("PRINT_SCAN", get_service_codes("আমার ডকুমেন্ট প্রিন্ট করতে হবে না"))

    def test_printer_information(self):
        self.assertNotIn("PRINT_SCAN", get_service_codes("How does a laser printer work?"))

    def test_scanner_tutorial(self):
        self.assertNotIn("PRINT_SCAN", get_service_codes("This tutorial explains how document scanners work"))

    def test_printing_industry_news(self):
        self.assertNotIn("PRINT_SCAN", get_service_codes("The printing industry is adopting new technologies"))

    def test_empty_input(self):
        self.assertNotIn("PRINT_SCAN", get_service_codes(""))


if __name__ == "__main__":
    unittest.main()
