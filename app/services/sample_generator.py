"""Generate synthetic orders for ShopLite demo."""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from app.brands import BRANDS
from app.models.schemas import OrderRecord

FALLBACK_PRODUCTS = {
    "skincare": ["GEN-SK01", "GEN-SK02"],
    "fashion": ["GEN-FA01", "GEN-FA02"],
    "home": ["GEN-HO01", "GEN-HO02"],
    "beauty": ["GEN-BE01", "GEN-BE02"],
}


def _pick_category(weights: dict[str, float]) -> str:
    categories = list(weights.keys())
    probs = [weights[c] for c in categories]
    return random.choices(categories, weights=probs, k=1)[0]


def _pick_product(brand_id: str, category: str) -> str:
    brand = BRANDS[brand_id]
    products = brand["categories"].get(category)
    if products:
        return random.choice(products)
    return random.choice(FALLBACK_PRODUCTS.get(category, ["GEN-ITEM"]))


def generate_sample_orders(seed: int = 42) -> list[OrderRecord]:
    random.seed(seed)
    start = datetime(2025, 1, 1)
    end = datetime(2026, 5, 1)
    span = (end - start).days

    orders: list[OrderRecord] = []
    order_counter = 1

    for brand_id, brand in BRANDS.items():
        users = [f"{brand_id}_user_{i:04d}" for i in range(1, 201)]
        target = brand["orders_target"]
        low, high = brand["price_range"]

        for _ in range(target):
            category = _pick_category(brand["category_weights"])
            product_id = _pick_product(brand_id, category)
            quantity = random.randint(1, 3)
            unit_price = round(random.uniform(low, high), 2)
            amount = round(unit_price * quantity, 2)
            order_time = start + timedelta(
                days=random.randint(0, span),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )

            orders.append(
                OrderRecord(
                    l2_tenant_id=brand_id,
                    order_id=f"ORD-{brand_id[:4].upper()}-{order_counter:06d}",
                    user_id=random.choice(users),
                    product_id=product_id,
                    category=category,
                    quantity=quantity,
                    amount=amount,
                    order_time=order_time,
                    channel=random.choice(brand["channels"]),
                )
            )
            order_counter += 1

    random.shuffle(orders)
    return orders
