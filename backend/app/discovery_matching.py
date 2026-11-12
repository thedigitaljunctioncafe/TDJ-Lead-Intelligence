"""Business and project discovery signals, separate from service intent."""

from .service_matching import normalize_text
from .service_matching_rules import SERVICE_MATCH_RULES

DISCOVERY_RULE_NAMES = (
    "new_retail_shop",
    "restaurant_cafe",
    "factory_manufacturing",
    "clinic_healthcare",
    "wholesaler_distributor",
    "real_estate_promoter",
    "housing_project",
)

DISCOVERY_LABELS = {
    "new_retail_shop": "Retail Shop",
    "restaurant_cafe": "Restaurant / Cafe",
    "factory_manufacturing": "Factory / Manufacturing",
    "clinic_healthcare": "Clinic / Healthcare",
    "wholesaler_distributor": "Wholesaler / Distributor",
    "real_estate_promoter": "Real Estate Promoter",
    "housing_project": "Housing / Apartment Project",
}


def match_discovery_signals(text: str) -> list[dict]:
    """Return business/project discovery signals without asserting service demand."""
    if not isinstance(text, str) or not text.strip():
        return []

    normalized_text = normalize_text(text)
    results = []

    for rule_name in DISCOVERY_RULE_NAMES:
        rule = SERVICE_MATCH_RULES.get(rule_name)
        if not rule:
            continue

        matched_keywords = sorted({
            keyword
            for keyword in rule["keywords"]
            if normalize_text(keyword) in normalized_text
        })

        if matched_keywords:
            results.append({
                "signal_type": "business_discovery",
                "discovery_code": rule_name,
                "label": DISCOVERY_LABELS[rule_name],
                "evidence_type": "keyword_signal",
                "matched_keywords": matched_keywords,
            })

    return results
