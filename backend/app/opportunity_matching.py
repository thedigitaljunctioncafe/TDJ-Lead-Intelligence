"""Potential service opportunities derived from discovery signals."""

OPPORTUNITY_MAP = {
    "new_retail_shop": {
        "TRADE_LICENSE": "Retail business may need trade licence assistance.",
        "GST": "Retail business may have GST registration or filing needs.",
        "WEBSITE": "A business website may be useful.",
    },
    "restaurant_cafe": {
        "TRADE_LICENSE": "Food business may need trade licence assistance.",
        "GST": "Restaurant may have GST registration or filing needs.",
        "WEBSITE": "An online presence may be useful.",
    },
    "factory_manufacturing": {
        "GST": "Manufacturing business may have GST compliance needs.",
        "TRADE_LICENSE": "Business licensing requirements may apply.",
        "WEBSITE": "A business website may be useful.",
    },
    "clinic_healthcare": {
        "TRADE_LICENSE": "Business licensing requirements may apply.",
        "WEBSITE": "A clinic website may be useful.",
    },
    "wholesaler_distributor": {
        "GST": "Wholesale business may have GST compliance needs.",
        "TRADE_LICENSE": "Business licensing requirements may apply.",
        "WEBSITE": "A business website may be useful.",
    },
    "real_estate_promoter": {
        "MUTATION": "Land mutation assistance may be relevant.",
        "PORCHA": "Land record assistance may be relevant.",
        "KHAJNA": "Land revenue payment assistance may be relevant.",
    },
    "housing_project": {
        "MUTATION": "Land mutation assistance may be relevant.",
        "PORCHA": "Land record assistance may be relevant.",
        "KHAJNA": "Land revenue payment assistance may be relevant.",
    },
}


def suggest_service_opportunities(discovery_signals: list[dict]) -> list[dict]:
    """Suggest potential services; never represent them as confirmed intent."""
    if not isinstance(discovery_signals, list):
        return []

    opportunities = {}

    for signal in discovery_signals:
        if not isinstance(signal, dict):
            continue

        discovery_code = signal.get("discovery_code")
        service_map = OPPORTUNITY_MAP.get(discovery_code, {})

        for service_code, reason in service_map.items():
            item = opportunities.setdefault(service_code, {
                "service_code": service_code,
                "opportunity_type": "potential_opportunity",
                "confirmed_intent": False,
                "based_on_discovery": [],
                "reasons": [],
            })

            if discovery_code not in item["based_on_discovery"]:
                item["based_on_discovery"].append(discovery_code)

            if reason not in item["reasons"]:
                item["reasons"].append(reason)

    return sorted(
        opportunities.values(),
        key=lambda item: item["service_code"],
    )
