
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
