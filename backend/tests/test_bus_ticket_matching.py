import unittest

from app.service_matching import match_services


def get_service_codes(text):
    return {item["service_code"] for item in match_services(text)}


class TestBusTicketMatching(unittest.TestCase):

    def test_need_bus_ticket_booking(self):
        self.assertIn("BUS_TICKET", get_service_codes("I need help booking a bus ticket"))

    def test_want_bus_ticket_booked(self):
        self.assertIn("BUS_TICKET", get_service_codes("I want someone to book my bus ticket"))

    def test_bengali_bus_ticket_booking(self):
        self.assertIn("BUS_TICKET", get_service_codes("আমার বাসের টিকিট বুক করা দরকার"))

    def test_bengali_bus_ticket_service(self):
        self.assertIn("BUS_TICKET", get_service_codes("আমি বাসের টিকিট বুক করাতে চাই"))

    def test_english_negative_bus_ticket(self):
        self.assertNotIn("BUS_TICKET", get_service_codes("I do not need bus ticket booking"))

    def test_bengali_negative_bus_ticket(self):
        self.assertNotIn("BUS_TICKET", get_service_codes("আমার বাসের টিকিট বুক করা দরকার নেই"))

    def test_generic_bus_schedule_information(self):
        self.assertNotIn("BUS_TICKET", get_service_codes("Bus schedules are available online"))

    def test_bus_ticket_booking_tutorial(self):
        self.assertNotIn("BUS_TICKET", get_service_codes("This tutorial explains how bus ticket booking works"))

    def test_bus_transport_news(self):
        self.assertNotIn("BUS_TICKET", get_service_codes("The government announced new bus transport rules"))

    def test_empty_input(self):
        self.assertNotIn("BUS_TICKET", get_service_codes(""))


if __name__ == "__main__":
    unittest.main()
