
"""
TDJ Lead Intelligence
Universal Lead-to-Service Matching Rules

These rules generate preliminary relevance signals.
A keyword match does not prove that a person or business
actually requires a service.

Supports English and Bengali keyword matching.
"""

SERVICE_MATCH_RULES = {

    # =====================================================
    # 1. BUSINESS CATEGORY INTELLIGENCE
    # =====================================================

    "new_retail_shop": {
        "keywords": [
            "retail shop",
            "new shop",
            "new store",
            "store",
            "showroom",
            "নতুন দোকান",
            "খুচরো দোকান",
            "শোরুম",
        ],
        "services": {
            "GST": 65,
            "TRADE_LICENSE": 85,
            "WEBSITE": 35,
        },
    },

    "restaurant_cafe": {
        "keywords": [
            "restaurant",
            "cafe",
            "food outlet",
            "bakery",
            "রেস্টুরেন্ট",
            "রেস্তোরাঁ",
            "ক্যাফে",
            "খাবারের দোকান",
        ],
        "services": {
            "GST": 70,
            "TRADE_LICENSE": 85,
            "WEBSITE": 60,
        },
    },

    "factory_manufacturing": {
        "keywords": [
            "factory",
            "manufacturing",
            "production unit",
            "manufacturing unit",
            "কারখানা",
            "উৎপাদন কেন্দ্র",
            "ফ্যাক্টরি",
        ],
        "services": {
            "GST": 85,
            "TRADE_LICENSE": 75,
            "WEBSITE": 65,
        },
    },

    "clinic_healthcare": {
        "keywords": [
            "clinic",
            "hospital",
            "diagnostic centre",
            "diagnostic center",
            "healthcare",
            "ক্লিনিক",
            "হাসপাতাল",
            "ডায়াগনস্টিক সেন্টার",
            "ডায়াগনস্টিক সেন্টার",
        ],
        "services": {
            "TRADE_LICENSE": 65,
            "WEBSITE": 65,
        },
    },

    "wholesaler_distributor": {
        "keywords": [
            "wholesaler",
            "wholesale business",
            "distributor",
            "bulk supplier",
            "পাইকারি ব্যবসা",
            "পাইকারি দোকান",
            "ডিস্ট্রিবিউটর",
        ],
        "services": {
            "GST": 85,
            "TRADE_LICENSE": 60,
            "WEBSITE": 50,
        },
    },

    # =====================================================
    # 2. REAL ESTATE & PROPERTY INTELLIGENCE
    # =====================================================

    "real_estate_promoter": {
        "keywords": [
            "real estate promoter",
            "real estate developer",
            "property developer",
            "property builder",
            "housing developer",
            "builder",
            "প্রোমোটার",
            "প্রপার্টি ডেভেলপার",
            "জমির প্রকল্প",
        ],
        "services": {
            "MUTATION": 55,
            "PORCHA": 55,
            "KHAJNA": 45,
        },
    },

    "housing_project": {
        "keywords": [
            "housing project",
            "apartment project",
            "residential project",
            "residential complex",
            "apartment complex",
            "আবাসন প্রকল্প",
            "ফ্ল্যাটের প্রকল্প",
            "অ্যাপার্টমেন্ট",
            "আবাসন",
        ],
        "services": {
            "MUTATION": 65,
            "PORCHA": 60,
            "KHAJNA": 45,
        },
    },

    # =====================================================
    # 3. WEBSITE DEVELOPMENT INTENT
    # =====================================================

    "website_requirement": {
        "keywords": [
            # English
            "need website",
            "need a website",
            "website required",
            "website developer",
            "website development",
            "looking for a website",
            "looking for website",
            "website for business",
            "need a website for my business",

            # Bengali
            "ওয়েবসাইট চাই",
            "ওয়েবসাইট চাই",
            "ওয়েবসাইট বানাতে চাই",
            "ওয়েবসাইট বানাতে চাই",
            "ওয়েবসাইট দরকার",
            "ওয়েবসাইট দরকার",
            "ওয়েবসাইট তৈরি করতে চাই",
            "ওয়েবসাইট তৈরি করতে চাই",
            "ওয়েবসাইট তৈরি করা দরকার",
            "ওয়েবসাইট তৈরি করা দরকার",
            "ওয়েবসাইট ডেভেলপার",
            "ওয়েবসাইট ডেভেলপার",
        ],
        "services": {
            "WEBSITE": 95,
        },
    },

    # =====================================================
    # 4. SOFTWARE DEVELOPMENT INTENT
    # =====================================================

    "software_requirement": {
        "keywords": [
            # English
            "need software",
            "software required",
            "software development",
            "looking for software",
            "billing software",
            "inventory software",
            "business management software",
            "custom software",

            # Bengali
            "সফটওয়্যার চাই",
            "সফটওয়্যার চাই",
            "সফটওয়্যার দরকার",
            "সফটওয়্যার দরকার",
            "সফটওয়্যার তৈরি করতে চাই",
            "সফটওয়্যার তৈরি করতে চাই",
            "বিলিং সফটওয়্যার",
            "বিলিং সফটওয়্যার",
        ],
        "services": {
            "SOFTWARE": 95,
        },
    },

    # =====================================================
    # 5. PAN CARD SERVICE INTENT
    # =====================================================

    "aadhaar_intent": {
        "keywords": [
            "need an aadhaar card",
            "need aadhaar card",
            "aadhaar card apply",
            "apply for aadhaar card",
            "aadhaar card required",
            "update my aadhaar",
            "need aadhaar update",
            "aadhaar update required",
            "looking to update aadhaar",
            "aadhaar correction",
            "aadhaar enrolment",
            "aadhaar enrollment",
            "\u0986\u09a7\u09be\u09b0 \u0995\u09be\u09b0\u09cd\u09a1 \u099a\u09be\u0987",
            "\u0986\u09a7\u09be\u09b0 \u0995\u09be\u09b0\u09cd\u09a1 \u0995\u09b0\u09a4\u09c7 \u099a\u09be\u0987",
            "\u0986\u09a7\u09be\u09b0 \u0995\u09be\u09b0\u09cd\u09a1 \u09a6\u09b0\u0995\u09be\u09b0",
            "\u0986\u09a7\u09be\u09b0 \u0995\u09be\u09b0\u09cd\u09a1 \u0986\u09aa\u09a1\u09c7\u099f",
            "\u0986\u09a7\u09be\u09b0 \u0986\u09aa\u09a1\u09c7\u099f \u0995\u09b0\u09a4\u09c7 \u099a\u09be\u0987",
            "\u0986\u09a7\u09be\u09b0 \u0995\u09be\u09b0\u09cd\u09a1 \u09b8\u0982\u09b6\u09cb\u09a7\u09a8",
            "\u0986\u09a7\u09be\u09b0 \u09b8\u0982\u09b6\u09cb\u09a7\u09a8 \u0995\u09b0\u09a4\u09c7 \u099a\u09be\u0987",
        ],
        "services": {"AADHAAR": 95},
    },
    "voter_intent": {
        "keywords": [
            "need a voter id card",
            "need voter id",
            "need a voter card",
            "apply for a voter card",
            "apply for voter id",
            "voter card apply",
            "voter id application",
            "voter id correction required",
            "need voter id correction",
            "\u09ad\u09cb\u099f\u09be\u09b0 \u0995\u09be\u09b0\u09cd\u09a1 \u099a\u09be\u0987",
            "\u09ad\u09cb\u099f\u09be\u09b0 \u0995\u09be\u09b0\u09cd\u09a1 \u0995\u09b0\u09a4\u09c7 \u099a\u09be\u0987",
            "\u09ad\u09cb\u099f\u09be\u09b0 \u0995\u09be\u09b0\u09cd\u09a1 \u09a6\u09b0\u0995\u09be\u09b0",
            "\u09ad\u09cb\u099f\u09be\u09b0 \u0986\u0987\u09a1\u09bf \u099a\u09be\u0987",
            "\u09ad\u09cb\u099f\u09be\u09b0 \u0995\u09be\u09b0\u09cd\u09a1 \u09b8\u0982\u09b6\u09cb\u09a7\u09a8 \u0995\u09b0\u09a4\u09c7 \u099a\u09be\u0987",
        ],
        "services": {"VOTER": 95},
    },
    "ration_intent": {
        "keywords": [
            "need a ration card",
            "need ration card",
            "apply for a ration card",
            "apply for ration card",
            "ration card application",
            "ration card required",
            "need ration card correction",
            "ration card correction required",
            "\u09b0\u09c7\u09b6\u09a8 \u0995\u09be\u09b0\u09cd\u09a1 \u099a\u09be\u0987",
            "\u09b0\u09c7\u09b6\u09a8 \u0995\u09be\u09b0\u09cd\u09a1 \u0995\u09b0\u09a4\u09c7 \u099a\u09be\u0987",
            "\u09b0\u09c7\u09b6\u09a8 \u0995\u09be\u09b0\u09cd\u09a1 \u09a6\u09b0\u0995\u09be\u09b0",
            "\u09b0\u09c7\u09b6\u09a8 \u0995\u09be\u09b0\u09cd\u09a1 \u0986\u09ac\u09c7\u09a6\u09a8 \u0995\u09b0\u09a4\u09c7 \u099a\u09be\u0987",
            "\u09b0\u09c7\u09b6\u09a8 \u0995\u09be\u09b0\u09cd\u09a1 \u09b8\u0982\u09b6\u09cb\u09a7\u09a8 \u0995\u09b0\u09a4\u09c7 \u099a\u09be\u0987",
        ],
        "services": {"RATION": 95},
    },
    "trade_license_intent": {
        "keywords": [
            "need a trade licence",
            "need trade licence",
            "need a trade license",
            "need trade license",
            "apply for a trade licence",
            "apply for trade licence",
            "apply for a trade license",
            "trade licence application",
            "trade license application",
            "trade licence required",
            "trade license required",
            "need trade licence renewal",
            "\u099f\u09cd\u09b0\u09c7\u09a1 \u09b2\u09be\u0987\u09b8\u09c7\u09a8\u09cd\u09b8 \u099a\u09be\u0987",
            "\u099f\u09cd\u09b0\u09c7\u09a1 \u09b2\u09be\u0987\u09b8\u09c7\u09a8\u09cd\u09b8 \u0995\u09b0\u09a4\u09c7 \u099a\u09be\u0987",
            "\u099f\u09cd\u09b0\u09c7\u09a1 \u09b2\u09be\u0987\u09b8\u09c7\u09a8\u09cd\u09b8 \u09a6\u09b0\u0995\u09be\u09b0",
            "\u099f\u09cd\u09b0\u09c7\u09a1 \u09b2\u09be\u0987\u09b8\u09c7\u09a8\u09cd\u09b8 \u0986\u09ac\u09c7\u09a6\u09a8 \u0995\u09b0\u09a4\u09c7 \u099a\u09be\u0987",
            "\u099f\u09cd\u09b0\u09c7\u09a1 \u09b2\u09be\u0987\u09b8\u09c7\u09a8\u09cd\u09b8 \u09a8\u09ac\u09be\u09af\u09bc\u09a8 \u0995\u09b0\u09a4\u09c7 \u099a\u09be\u0987",
        ],
        "services": {"TRADE_LICENSE": 95},
    },
    "driving_license_intent": {
        "keywords": [
            "need a driving licence",
            "need driving licence",
            "need a driving license",
            "need driving license",
            "apply for a driving licence",
            "apply for driving licence",
            "apply for a driving license",
            "driving licence application",
            "driving license application",
            "driving licence required",
            "driving license required",
            "need driving licence renewal",
            "need learner licence",
            "apply for learner licence",
            "\u09a1\u09cd\u09b0\u09be\u0987\u09ad\u09bf\u0982 \u09b2\u09be\u0987\u09b8\u09c7\u09a8\u09cd\u09b8 \u099a\u09be\u0987",
            "\u09a1\u09cd\u09b0\u09be\u0987\u09ad\u09bf\u0982 \u09b2\u09be\u0987\u09b8\u09c7\u09a8\u09cd\u09b8 \u0995\u09b0\u09a4\u09c7 \u099a\u09be\u0987",
            "\u09a1\u09cd\u09b0\u09be\u0987\u09ad\u09bf\u0982 \u09b2\u09be\u0987\u09b8\u09c7\u09a8\u09cd\u09b8 \u09a6\u09b0\u0995\u09be\u09b0",
            "\u09a1\u09cd\u09b0\u09be\u0987\u09ad\u09bf\u0982 \u09b2\u09be\u0987\u09b8\u09c7\u09a8\u09cd\u09b8 \u0986\u09ac\u09c7\u09a6\u09a8 \u0995\u09b0\u09a4\u09c7 \u099a\u09be\u0987",
            "\u09a1\u09cd\u09b0\u09be\u0987\u09ad\u09bf\u0982 \u09b2\u09be\u0987\u09b8\u09c7\u09a8\u09cd\u09b8 \u09a8\u09ac\u09be\u09af\u09bc\u09a8 \u0995\u09b0\u09a4\u09c7 \u099a\u09be\u0987",
            "\u09b2\u09be\u09b0\u09cd\u09a8\u09be\u09b0 \u09b2\u09be\u0987\u09b8\u09c7\u09a8\u09cd\u09b8 \u099a\u09be\u0987",
        ],
        "services": {"DRIVING_LICENSE": 95},
    },
    "online_form_intent": {
        "keywords": [
            "need help with online form filling",
            "need online form filling",
            "need help filling online form",
            "want someone to fill my online application form",
            "need someone to fill my form",
            "need online application assistance",
            "online form filling service required",
            "looking for online form filling service",
            "\u0985\u09a8\u09b2\u09be\u0987\u09a8 \u09ab\u09b0\u09cd\u09ae \u09aa\u09c2\u09b0\u09a3 \u0995\u09b0\u09be \u09a6\u09b0\u0995\u09be\u09b0",
            "\u0985\u09a8\u09b2\u09be\u0987\u09a8 \u09ab\u09b0\u09cd\u09ae \u09ab\u09bf\u09b2\u0986\u09aa \u0995\u09b0\u09be\u09a4\u09c7 \u099a\u09be\u0987",
            "\u0985\u09a8\u09b2\u09be\u0987\u09a8 \u09ab\u09b0\u09cd\u09ae \u09aa\u09c2\u09b0\u09a3 \u0995\u09b0\u09c7 \u09a6\u09bf\u09a4\u09c7 \u09b9\u09ac\u09c7",
            "\u09ab\u09b0\u09cd\u09ae \u09ab\u09bf\u09b2\u0986\u09aa \u0995\u09b0\u09be\u09a4\u09c7 \u099a\u09be\u0987",
            "\u0985\u09a8\u09b2\u09be\u0987\u09a8 \u0986\u09ac\u09c7\u09a6\u09a8 \u0995\u09b0\u09c7 \u09a6\u09bf\u09a4\u09c7 \u09b9\u09ac\u09c7",
        ],
        "services": {"ONLINE_FORM": 95},
    },
    "rail_ticket_intent": {
        "keywords": [
            "need help booking a train ticket",
            "need to book a train ticket",
            "need train ticket booking",
            "book my railway ticket",
            "want someone to book my railway ticket",
            "book a railway ticket",
            "want to book a train ticket",
            "train ticket booking for me",
            "\u099f\u09cd\u09b0\u09c7\u09a8\u09c7\u09b0 \u099f\u09bf\u0995\u09bf\u099f \u09ac\u09c1\u0995 \u0995\u09b0\u09be \u09a6\u09b0\u0995\u09be\u09b0",
            "\u099f\u09cd\u09b0\u09c7\u09a8\u09c7\u09b0 \u099f\u09bf\u0995\u09bf\u099f \u09ac\u09c1\u0995 \u0995\u09b0\u09be\u09a4\u09c7 \u099a\u09be\u0987",
        ],
        "services": {"RAIL_TICKET": 95},
    },
    "air_ticket_intent": {
        "keywords": [
            "need help booking a flight ticket",
            "need to book a flight ticket",
            "need flight ticket booking",
            "book my flight ticket",
            "want someone to book my flight ticket",
            "book an air ticket",
            "want to book a flight ticket",
            "flight ticket booking for me",
            "\u09ac\u09bf\u09ae\u09be\u09a8\u09c7\u09b0 \u099f\u09bf\u0995\u09bf\u099f \u09ac\u09c1\u0995 \u0995\u09b0\u09be \u09a6\u09b0\u0995\u09be\u09b0",
            "\u09aa\u09cd\u09b2\u09c7\u09a8\u09c7\u09b0 \u099f\u09bf\u0995\u09bf\u099f \u09ac\u09c1\u0995 \u0995\u09b0\u09be\u09a4\u09c7 \u099a\u09be\u0987",
        ],
        "services": {"AIR_TICKET": 95},
    },
    "bus_ticket_intent": {
        "keywords": [
            "need help booking a bus ticket",
            "need to book a bus ticket",
            "need bus ticket booking",
            "book my bus ticket",
            "want someone to book my bus ticket",
            "want to book a bus ticket",
            "bus ticket booking for me",
            "\u09ac\u09be\u09b8\u09c7\u09b0 \u099f\u09bf\u0995\u09bf\u099f \u09ac\u09c1\u0995 \u0995\u09b0\u09be \u09a6\u09b0\u0995\u09be\u09b0",
            "\u09ac\u09be\u09b8\u09c7\u09b0 \u099f\u09bf\u0995\u09bf\u099f \u09ac\u09c1\u0995 \u0995\u09b0\u09be\u09a4\u09c7 \u099a\u09be\u0987",
        ],
        "services": {"BUS_TICKET": 95},
    },
    "print_scan_intent": {
        "keywords": [
            "need document printing service",
            "need someone to scan my documents",
            "need document scanning service",
            "want my documents printed",
            "want my documents scanned",
            "document printing for me",
            "\u09a1\u0995\u09c1\u09ae\u09c7\u09a8\u09cd\u099f \u09aa\u09cd\u09b0\u09bf\u09a8\u09cd\u099f \u0995\u09b0\u09a4\u09c7 \u09b9\u09ac\u09c7",
            "\u09a1\u0995\u09c1\u09ae\u09c7\u09a8\u09cd\u099f \u09b8\u09cd\u0995\u09cd\u09af\u09be\u09a8 \u0993 \u09aa\u09cd\u09b0\u09bf\u09a8\u09cd\u099f \u0995\u09b0\u09c7 \u09a6\u09bf\u09a4\u09c7 \u09b9\u09ac\u09c7",
        ],
        "services": {"PRINT_SCAN": 95},
    },
    "pan_intent": {
        "keywords": [
            # English
            "need pan card",
            "pan card apply",
            "pan application",
            "apply for pan card",
            "pan card required",

            # Bengali
            "প্যান কার্ড চাই",
            "প্যান কার্ড করতে চাই",
            "প্যান কার্ড দরকার",
            "প্যান কার্ড বানাতে চাই",
        ],
        "services": {
            "PAN": 95,
        },
    },

    # =====================================================
    # 6. PASSPORT SERVICE INTENT
    # =====================================================

    "passport_intent": {
        "keywords": [
            # English
            "need passport",
            "passport apply",
            "passport application",
            "apply for passport",
            "passport required",

            # Bengali
            "পাসপোর্ট চাই",
            "পাসপোর্ট করতে চাই",
            "পাসপোর্ট দরকার",
            "পাসপোর্ট বানাতে চাই",
        ],
        "services": {
            "PASSPORT": 95,
        },
    },

    # =====================================================
    # 7. GST SERVICE INTENT
    # =====================================================

    "gst_intent": {
        "keywords": [
            # English
            "need gst",
            "gst registration",
            "gst filing",
            "gst return filing",
            "apply for gst",
            "gst required",

            # Bengali
            "জিএসটি চাই",
            "জিএসটি রেজিস্ট্রেশন",
            "জিএসটি ফাইলিং",
            "জিএসটি করতে চাই",
            "জিএসটি দরকার",
        ],
        "services": {
            "GST": 95,
        },
    },

    # =====================================================
    # 8. INCOME TAX RETURN SERVICE INTENT
    # =====================================================

    "itr_intent": {
        "keywords": [
            # English
            "need itr",
            "itr filing",
            "income tax return filing",
            "file income tax return",
            "need income tax return",

            # Bengali
            "আইটিআর চাই",
            "আইটিআর ফাইলিং",
            "ইনকাম ট্যাক্স রিটার্ন ফাইলিং",
        ],
        "services": {
            "ITR": 95,
        },
    },

    # =====================================================
    # 9. PORCHA SERVICE INTENT
    # =====================================================

    "porcha_intent": {
        "keywords": [
            # English
            "need porcha",
            "porcha required",
            "porcha application",
            "get land porcha",

            # Bengali
            "পর্চা চাই",
            "পর্চা দরকার",
            "পর্চা তুলতে চাই",
            "জমির পর্চা",
        ],
        "services": {
            "PORCHA": 95,
        },
    },

    # =====================================================
    # 10. LAND MUTATION SERVICE INTENT
    # =====================================================

    "mutation_intent": {
        "keywords": [
            # English
            "need land mutation",
            "land mutation required",
            "mutation application",
            "apply for land mutation",

            # Bengali
            "জমির মিউটেশন",
            "জমি নামজারি করতে চাই",
            "নামজারি দরকার",
            "জমির নামজারি",
        ],
        "services": {
            "MUTATION": 95,
        },
    },

    # =====================================================
    # 11. KHAJNA PAYMENT SERVICE INTENT
    # =====================================================

    "khajna_intent": {
        "keywords": [
            # English
            "need khajna payment",
            "pay land revenue",
            "khajna payment required",

            # Bengali
            "খাজনা দিতে চাই",
            "খাজনা জমা দিতে চাই",
            "খাজনা দেওয়া দরকার",
            "খাজনা পেমেন্ট",
            "জমির খাজনা দিতে হবে",
        ],
        "services": {
            "KHAJNA": 95,
        },
    },
}
