import unittest

from app.discovery_matching import match_discovery_signals
from app.opportunity_matching import suggest_service_opportunities


class TestBusinessDiscovery(unittest.TestCase):

    def test_new_retail_shop(self):
        results = match_discovery_signals("A new retail shop opened recently")
        self.assertIn("new_retail_shop", [x["discovery_code"] for x in results])

    def test_restaurant(self):
        results = match_discovery_signals("A new restaurant opened")
        self.assertIn("restaurant_cafe", [x["discovery_code"] for x in results])

    def test_factory(self):
        results = match_discovery_signals("A manufacturing factory started production")
        self.assertIn("factory_manufacturing", [x["discovery_code"] for x in results])

    def test_clinic(self):
        results = match_discovery_signals("A new clinic opened")
        self.assertIn("clinic_healthcare", [x["discovery_code"] for x in results])

    def test_wholesaler(self):
        results = match_discovery_signals("A wholesale business and distributor")
        self.assertIn("wholesaler_distributor", [x["discovery_code"] for x in results])

    def test_real_estate_promoter(self):
        results = match_discovery_signals("A real estate promoter announced a project")
        self.assertIn("real_estate_promoter", [x["discovery_code"] for x in results])

    def test_housing_project(self):
        results = match_discovery_signals("A new housing project was announced")
        self.assertIn("housing_project", [x["discovery_code"] for x in results])

    def test_discovery_does_not_claim_service_intent(self):
        results = match_discovery_signals("A new retail shop opened")
        for item in results:
            self.assertEqual(item["signal_type"], "business_discovery")
            self.assertNotIn("service_code", item)

    def test_empty_input(self):
        self.assertEqual(match_discovery_signals(""), [])
        self.assertEqual(match_discovery_signals("   "), [])
        self.assertEqual(match_discovery_signals(None), [])


class TestServiceOpportunities(unittest.TestCase):

    def test_retail_opportunities_are_potential(self):
        signals = match_discovery_signals("A new retail shop opened")
        results = suggest_service_opportunities(signals)

        self.assertTrue(results)
        for item in results:
            self.assertEqual(item["opportunity_type"], "potential_opportunity")
            self.assertFalse(item["confirmed_intent"])

    def test_opportunity_does_not_claim_customer_demand(self):
        signals = match_discovery_signals("A new restaurant opened")
        results = suggest_service_opportunities(signals)

        self.assertTrue(results)
        self.assertTrue(all(item["confirmed_intent"] is False for item in results))

    def test_duplicate_discovery_signals_do_not_duplicate_opportunities(self):
        signals = match_discovery_signals("A new retail shop opened")
        results = suggest_service_opportunities(signals + signals)

        codes = [item["service_code"] for item in results]
        self.assertEqual(len(codes), len(set(codes)))

    def test_unknown_discovery_has_no_opportunity(self):
        results = suggest_service_opportunities([
            {"discovery_code": "unknown_category"}
        ])
        self.assertEqual(results, [])

    def test_invalid_input(self):
        self.assertEqual(suggest_service_opportunities(None), [])
        self.assertEqual(suggest_service_opportunities([]), [])


if __name__ == "__main__":
    unittest.main()
