import unittest

from app.service_matching import match_services


def get_service_codes(text):
    return {item["service_code"] for item in match_services(text)}


class TestRailTicketMatching(unittest.TestCase):

    def test_need_train_ticket_booking(self):
        self.assertIn("RAIL_TICKET", get_service_codes("I need help booking a train ticket"))

    def test_want_train_ticket_booked(self):
        self.assertIn("RAIL_TICKET", get_service_codes("I want someone to book my railway ticket"))

    def test_bengali_train_ticket_booking(self):
        self.assertIn("RAIL_TICKET", get_service_codes("আমার ট্রেনের টিকিট বুক করা দরকার"))

    def test_bengali_ticket_booking_service(self):
        self.assertIn("RAIL_TICKET", get_service_codes("আমি ট্রেনের টিকিট বুক করাতে চাই"))

    def test_english_negative_train_ticket(self):
        self.assertNotIn("RAIL_TICKET", get_service_codes("I do not need train ticket booking"))

    def test_bengali_negative_train_ticket(self):
        self.assertNotIn("RAIL_TICKET", get_service_codes("আমার ট্রেনের টিকিট বুক করা দরকার নেই"))

    def test_generic_train_schedule_information(self):
        self.assertNotIn("RAIL_TICKET", get_service_codes("Train schedules are available online"))

    def test_train_ticket_booking_tutorial(self):
        self.assertNotIn("RAIL_TICKET", get_service_codes("This tutorial explains how train ticket booking works"))

    def test_railway_ticket_news(self):
        self.assertNotIn("RAIL_TICKET", get_service_codes("Indian Railways announced new ticket booking rules"))

    def test_empty_input(self):
        self.assertNotIn("RAIL_TICKET", get_service_codes(""))


if __name__ == "__main__":
    unittest.main()
