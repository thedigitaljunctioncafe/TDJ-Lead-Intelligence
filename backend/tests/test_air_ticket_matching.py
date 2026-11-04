import unittest

from app.service_matching import match_services


def get_service_codes(text):
    return {item["service_code"] for item in match_services(text)}


class TestAirTicketMatching(unittest.TestCase):

    def test_need_air_ticket_booking(self):
        self.assertIn("AIR_TICKET", get_service_codes("I need help booking a flight ticket"))

    def test_want_flight_ticket_booked(self):
        self.assertIn("AIR_TICKET", get_service_codes("I want someone to book my flight ticket"))

    def test_bengali_air_ticket_booking(self):
        self.assertIn("AIR_TICKET", get_service_codes("আমার বিমানের টিকিট বুক করা দরকার"))

    def test_bengali_flight_ticket_service(self):
        self.assertIn("AIR_TICKET", get_service_codes("আমি প্লেনের টিকিট বুক করাতে চাই"))

    def test_english_negative_air_ticket(self):
        self.assertNotIn("AIR_TICKET", get_service_codes("I do not need flight ticket booking"))

    def test_bengali_negative_air_ticket(self):
        self.assertNotIn("AIR_TICKET", get_service_codes("আমার বিমানের টিকিট বুক করা দরকার নেই"))

    def test_generic_flight_schedule_information(self):
        self.assertNotIn("AIR_TICKET", get_service_codes("Flight schedules are available online"))

    def test_air_ticket_booking_tutorial(self):
        self.assertNotIn("AIR_TICKET", get_service_codes("This tutorial explains how flight ticket booking works"))

    def test_airline_news(self):
        self.assertNotIn("AIR_TICKET", get_service_codes("Airlines announced new baggage rules"))

    def test_empty_input(self):
        self.assertNotIn("AIR_TICKET", get_service_codes(""))


if __name__ == "__main__":
    unittest.main()
