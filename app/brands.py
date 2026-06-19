"""Brand catalog for ShopLite demo data."""

BRANDS = {
    "aura_beauty": {
        "display_name": "Aura Beauty",
        "categories": {
            "skincare": ["AB-SK01", "AB-SK02", "AB-SK03", "AB-SK04"],
            "beauty": ["AB-BE01", "AB-BE02", "AB-BE03"],
        },
        "category_weights": {"skincare": 0.5, "beauty": 0.4, "fashion": 0.05, "home": 0.05},
        "channels": ["website", "shopee", "instagram"],
        "price_range": (499, 3280),
        "orders_target": 700,
    },
    "loom_fashion": {
        "display_name": "Loom Fashion",
        "categories": {
            "fashion": ["LF-FA01", "LF-FA02", "LF-FA03", "LF-FA04", "LF-FA05"],
            "beauty": ["LF-BE01", "LF-BE02"],
        },
        "category_weights": {"fashion": 0.72, "beauty": 0.15, "skincare": 0.08, "home": 0.05},
        "channels": ["website", "shopee"],
        "price_range": (690, 4980),
        "orders_target": 650,
    },
    "nest_home": {
        "display_name": "Nest Home",
        "categories": {
            "home": ["NH-HO01", "NH-HO02", "NH-HO03", "NH-HO04"],
            "fashion": ["NH-FA01", "NH-FA02"],
        },
        "category_weights": {"home": 0.7, "fashion": 0.18, "skincare": 0.07, "beauty": 0.05},
        "channels": ["website", "shopee", "instagram"],
        "price_range": (399, 5680),
        "orders_target": 650,
    },
}

ALL_CATEGORIES = ["skincare", "fashion", "home", "beauty"]

BRAND_LIST = [
    {"id": brand_id, "name": meta["display_name"]}
    for brand_id, meta in BRANDS.items()
]

PRODUCT_NAMES = {
    "AB-SK01": "玻尿酸精華",
    "AB-SK02": "維他命 C 精華",
    "AB-SK03": "修護精華油",
    "AB-SK04": "敏感肌化妝水",
    "AB-BE01": "霧面唇釉",
    "AB-BE02": "柔光粉底",
    "AB-BE03": "防曬隔離乳",
    "LF-FA01": "亞麻襯衫",
    "LF-FA02": "直筒牛仔褲",
    "LF-FA03": "針織外套",
    "LF-FA04": "休閒西裝褲",
    "LF-FA05": "棉質 T 恤",
    "LF-BE01": "護手霜",
    "LF-BE02": "身體乳",
    "NH-HO01": "北歐抱枕",
    "NH-HO02": "香氛蠟燭",
    "NH-HO03": "收納籃組",
    "NH-HO04": "亞麻床包組",
    "NH-FA01": "居家拖鞋",
    "NH-FA02": "棉麻圍裙",
}

CHANNEL_LABELS = {
    "website": "官網",
    "shopee": "蝦皮",
    "instagram": "Instagram",
}


def get_product_name(product_id: str) -> str:
    return PRODUCT_NAMES.get(product_id, product_id)


def get_channel_label(channel: str) -> str:
    return CHANNEL_LABELS.get(channel, channel)
