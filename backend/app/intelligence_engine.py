"""Unified intelligence engine: discovery, confirmed intent and opportunities."""

from .discovery_matching import (
    DISCOVERY_RULE_NAMES,
    match_discovery_signals,
)
from .opportunity_matching import suggest_service_opportunities
from .service_matching import normalize_text, has_negative_intent
from .service_matching_rules import SERVICE_MATCH_RULES


def match_confirmed_service_intents(text: str) -> list[dict]:
    """Match only service-intent rules, excluding business discovery rules."""
    if not isinstance(text, str) or not text.strip():
        return []

    normalized_text = normalize_text(text)
    matches = {}

    for rule_name, rule in SERVICE_MATCH_RULES.items():
        if rule_name in DISCOVERY_RULE_NAMES:
            continue

        matched_keywords = [
            keyword
            for keyword in rule["keywords"]
            if normalize_text(keyword) in normalized_text
        ]

        if not matched_keywords:
            continue

        for service_code, score in rule["services"].items():
            valid_evidence = [
                keyword
                for keyword in matched_keywords
                if not has_negative_intent(
                    normalized_text, normalize_text(keyword)
                )
            ]

            if not valid_evidence:
                continue

            current = matches.get(service_code)

            if current is None:
                matches[service_code] = {
                    "service_code": service_code,
                    "relevance_score": float(score),
                    "confidence": "keyword_signal",
                    "matched_rules": [rule_name],
                    "matched_keywords": sorted(set(valid_evidence)),
                    "match_reason": "",
                    "intent_type": "confirmed_service_intent",
                }
            else:
                current["relevance_score"] = max(
                    current["relevance_score"], float(score)
                )
                if rule_name not in current["matched_rules"]:
                    current["matched_rules"].append(rule_name)
                current["matched_keywords"] = sorted(
                    set(current["matched_keywords"] + valid_evidence)
                )

    results = []
    for match in matches.values():
        match["match_reason"] = (
            "Rules: " + ", ".join(match["matched_rules"])
            + "; Evidence: " + ", ".join(match["matched_keywords"])
        )
        results.append(match)

    return sorted(
        results,
        key=lambda item: item["relevance_score"],
        reverse=True,
    )


def analyze_text(text: str) -> dict:
    """Return three independent intelligence result groups."""
    discovery_signals = match_discovery_signals(text)
    confirmed_intents = match_confirmed_service_intents(text)
    opportunities = suggest_service_opportunities(discovery_signals)

    return {
        "discovery_signals": discovery_signals,
        "confirmed_service_intents": confirmed_intents,
        "potential_opportunities": opportunities,
        "summary": {
            "discovery_count": len(discovery_signals),
            "confirmed_intent_count": len(confirmed_intents),
            "potential_opportunity_count": len(opportunities),
        },
    }
