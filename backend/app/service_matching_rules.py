
"""
TDJ Lead Intelligence
Universal Lead-to-Service Matching Rules

Rules are preliminary relevance signals, not proof
that a person or business requires a service.
"""

SERVICE_MATCH_RULES = {
    "new_retail_shop": {
        "keywords": ["retail shop", "new shop", "store", "showroom", "নতুন দোকান", "খুচরো দোকান", "শোরুম"],
        "services": {
            "GST": 65,
            "TRADE_LICENSE": 85,
            "WEBSITE": 35,
        },
    },
    "restaurant_cafe": {
        "keywords": ["restaurant", "cafe", "food outlet", "bakery", "রেস্টুরেন্ট", "রেস্তোরাঁ", "ক্যাফে", "খাবারের দোকান"],
        "services": {
            "GST": 70,
            "TRADE_LICENSE": 85,
            "WEBSITE": 60,
        },
    },
    "factory_manufacturing": {
        "keywords": ["factory", "manufacturing", "production unit","কারখানা", "উৎপাদন কেন্দ্র", "ফ্যাক্টরি"],
        "services": {
            "GST": 85,
            "TRADE_LICENSE": 75,
            "WEBSITE": 65,
        },
    },
    "clinic_healthcare": {
        "keywords": ["clinic", "hospital", "diagnostic centre", "healthcare", "ক্লিনিক", "হাসপাতাল", "ডায়াগনস্টিক সেন্টার"],
        "services": {
            "TRADE_LICENSE": 65,
            "WEBSITE": 65,
        },
    },
    "wholesaler_distributor": {
        "keywords": ["wholesaler", "distributor", "bulk supplier", "পাইকারি ব্যবসা", "ডিস্ট্রিবিউটর"],
        "services": {
            "GST": 85,
            "TRADE_LICENSE": 60,
            "WEBSITE": 50,
        },
    },
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
        "keywords": ["housing project", "apartment project", "residential project", "আবাসন প্রকল্প", "ফ্ল্যাটের প্রকল্প", "অ্যাপার্টমেন্ট"],
        "services": {
            "MUTATION": 65,
            "PORCHA": 60,
            "KHAJNA": 45,
        },
    },
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

        # Bengali positive intent
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
    ],
    "services": {"WEBSITE": 95},
    },
    "software_requirement": {
        "keywords": ["need software", "billing software", "software required", "সফটওয়্যার চাই", "বিলিং সফটওয়্যার", "সফটওয়্যার দরকার"],
        "services": {"SOFTWARE": 95},
    },
    "pan_intent": {
        "keywords": ["need pan card", "pan card apply", "pan application", "প্যান কার্ড চাই", "প্যান কার্ড করতে চাই"],
        "services": {"PAN": 95},
    },
    "passport_intent": {
        "keywords": ["need passport", "passport apply", "passport application", "পাসপোর্ট চাই", "পাসপোর্ট করতে চাই"],
        "services": {"PASSPORT": 95},
    },
    "gst_intent": {
        "keywords": ["need gst", "gst registration", "gst filing", "জিএসটি চাই", "জিএসটি রেজিস্ট্রেশন", "জিএসটি ফাইলিং"],
        "services": {"GST": 95},
    },
    "itr_intent": {
        "keywords": ["need itr", "income tax return", "itr filing", "আইটিআর চাই", "ইনকাম ট্যাক্স রিটার্ন", "আইটিআর ফাইলিং"],
        "services": {"ITR": 95},
    },
    "land_record_intent": {
        "keywords": ["need porcha", "land record", "land mutation", "পর্চা চাই", "জমির মিউটেশন", "খাজনা দিতে চাই"],
        "services": {
            "PORCHA": 95,
            "MUTATION": 85,
        },
    },
}
