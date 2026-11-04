
"""
TDJ Lead Intelligence - Enhanced Service Matching Engine
Supports Bengali + English, negative intent and evidence aggregation.
"""

import re
from .service_matching_rules import SERVICE_MATCH_RULES


NEGATIVE_PATTERNS = [
    r"\bnot interested in\b",
    r"\bdo not need\b",
    r"\bdon't need\b",
    r"\bdoes not need\b",
    r"\bno need for\b",
    r"\bnot looking for\b",
    r"\bnever need\b",
    r"\bnot required\b",
    r"\bচাই না\b",
    r"\bলাগবে না\b",
    r"\bপ্রয়োজন নেই\b",
    r"\bদরকার নেই\b",
    r"\bকরতে চাই না\b",
    r"\bইচ্ছা নেই\b",
]

def normalize_text(text: str) -> str:
    text = text.casefold()
    text = re.sub(r"\s+", " ", text)
    return text.strip()




def has_negative_intent(text: str, keyword: str) -> bool:
    text = normalize_text(text)
    keyword = normalize_text(keyword)

    start = 0

    english_negative_before = [
        r"(?:do not|don't|dont|does not|doesn't)\s*$",
        r"(?:do not|don't|dont|does not|doesn't)\s+need\s*$",
        r"not interested in\s*$",
        r"not looking for\s*$",
        r"no need for\s*$",
    ]

    bengali_negative_after = (
        "\u09a8\u09be",
        "\u09a8\u09c7\u0987",
        "\u09b2\u09be\u0997\u09ac\u09c7 \u09a8\u09be",
        "\u099a\u09be\u0987 \u09a8\u09be",
        "\u09a6\u09b0\u0995\u09be\u09b0 \u09a8\u09c7\u0987",
        "\u09aa\u09cd\u09b0\u09af\u09bc\u09cb\u099c\u09a8 \u09a8\u09c7\u0987",
        "\u0995\u09b0\u09a4\u09c7 \u099a\u09be\u0987 \u09a8\u09be",
        "\u09a6\u09bf\u09a4\u09c7 \u099a\u09be\u0987 \u09a8\u09be",
        "\u09a4\u09c1\u09b2\u09a4\u09c7 \u099a\u09be\u0987 \u09a8\u09be",
        "\u0995\u09b0\u09a4\u09c7 \u09b9\u09ac\u09c7 \u09a8\u09be",
        "\u09a6\u09bf\u09a4\u09c7 \u09b9\u09ac\u09c7 \u09a8\u09be",
        "\u09a4\u09c8\u09b0\u09bf \u0995\u09b0\u09a4\u09c7 \u099a\u09be\u0987 \u09a8\u09be",
        "\u09ac\u09be\u09a8\u09be\u09a4\u09c7 \u099a\u09be\u0987 \u09a8\u09be",
        "\u09a4\u09c8\u09b0\u09bf \u0995\u09b0\u09be \u09a6\u09b0\u0995\u09be\u09b0 \u09a8\u09c7\u0987",
        "\u0995\u09b0\u09be\u09b0 \u09a6\u09b0\u0995\u09be\u09b0 \u09a8\u09c7\u0987",
    )

    while True:
        position = text.find(keyword, start)
        if position == -1:
            break

        end = position + len(keyword)
        before = text[max(0, position - 50):position]
        after = text[end:end + 60].lstrip()

        if any(
            re.search(pattern, before, re.IGNORECASE)
            for pattern in english_negative_before
        ):
            return True

        if after.startswith(bengali_negative_after):
            return True

        start = end

    return False

def match_services(text: str) -> list[dict]:
    if not isinstance(text, str) or not text.strip():
        return []

    normalized_text = normalize_text(text)
    matches = {}

    for rule_name, rule in SERVICE_MATCH_RULES.items():
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
                if not has_negative_intent(normalized_text, normalize_text(keyword))
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
                    "matched_keywords": valid_evidence,
                    "match_reason": "",
                }
            else:
                current["relevance_score"] = max(
                    current["relevance_score"],
                    float(score),
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
