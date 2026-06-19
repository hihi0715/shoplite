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
