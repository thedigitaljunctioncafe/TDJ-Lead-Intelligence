import unittest

from app.intelligence_engine import (
    analyze_text,
    match_confirmed_service_intents,
)


class TestUnifiedIntelligenceEngine(unittest.TestCase):

    def test_new_shop_is_discovery_not_confirmed_demand(self):
        result = analyze_text("A new retail shop opened recently")
        self.assertTrue(result["discovery_signals"])
        self.assertEqual(result["confirmed_service_intents"], [])
        self.assertTrue(result["potential_opportunities"])
        self.assertTrue(all(
            item["confirmed_intent"] is False
            for item in result["potential_opportunities"]
        ))

    def test_explicit_gst_request_is_confirmed_intent(self):
        result = analyze_text("I need GST registration for my business")
        codes = [
            item["service_code"]
            for item in result["confirmed_service_intents"]
        ]
        self.assertIn("GST", codes)

    def test_business_and_explicit_intent_are_separate(self):
        result = analyze_text(
            "A new restaurant opened. I need GST registration."
        )
        self.assertTrue(result["discovery_signals"])
        self.assertIn(
            "GST",
            [x["service_code"] for x in result["confirmed_service_intents"]]
        )
        self.assertTrue(result["potential_opportunities"])

    def test_discovery_rules_never_become_confirmed_intents(self):
        result = analyze_text("A new factory manufacturing unit opened")
        codes = [
            item["service_code"]
            for item in result["confirmed_service_intents"]
        ]
        self.assertNotIn("GST", codes)
        self.assertNotIn("TRADE_LICENSE", codes)
        self.assertNotIn("WEBSITE", codes)

    def test_bengali_explicit_website_intent(self):
        result = analyze_text(
            "\u0986\u09ae\u09be\u09b0 "
            "\u09ac\u09cd\u09af\u09ac\u09b8\u09be\u09b0 "
            "\u099c\u09a8\u09cd\u09af "
            "\u098f\u0995\u099f\u09be "
            "\u0993\u09df\u09c7\u09ac\u09b8\u09be\u0987\u099f "
            "\u099a\u09be\u0987"
        )
        codes = [
            item["service_code"]
            for item in result["confirmed_service_intents"]
        ]
        self.assertIn("WEBSITE", codes)

    def test_bengali_negative_intent_is_not_confirmed(self):
        result = analyze_text(
            "\u0986\u09ae\u09be\u09b0 "
            "\u099c\u09ae\u09bf\u09b0 "
            "\u09ae\u09bf\u0989\u099f\u09c7\u09b6\u09a8 "
            "\u0995\u09b0\u09a4\u09c7 "
            "\u099a\u09be\u0987 \u09a8\u09be"
        )
        codes = [
            item["service_code"]
            for item in result["confirmed_service_intents"]
        ]
        self.assertNotIn("MUTATION", codes)

    def test_empty_input(self):
        result = analyze_text("")
        self.assertEqual(result["discovery_signals"], [])
        self.assertEqual(result["confirmed_service_intents"], [])
        self.assertEqual(result["potential_opportunities"], [])
        self.assertEqual(result["summary"]["discovery_count"], 0)

    def test_direct_intent_matcher_excludes_discovery_rules(self):
        results = match_confirmed_service_intents(
            "A new retail shop opened"
        )
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
