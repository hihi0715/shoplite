"""Generate synthetic e-commerce orders for ShopLite demo."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.sample_generator import generate_sample_orders


def main() -> None:
    data_dir = ROOT / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    orders = generate_sample_orders()
    csv_path = data_dir / "sample_orders.csv"
    json_path = data_dir / "sample_orders.json"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "l2_tenant_id",
                "order_id",
                "user_id",
                "product_id",
                "category",
                "quantity",
                "amount",
                "order_time",
                "channel",
            ],
        )
        writer.writeheader()
        for order in orders:
            writer.writerow(
                {
                    "l2_tenant_id": order.l2_tenant_id,
                    "order_id": order.order_id,
                    "user_id": order.user_id,
                    "product_id": order.product_id,
                    "category": order.category,
                    "quantity": order.quantity,
                    "amount": order.amount,
                    "order_time": order.order_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "channel": order.channel,
                }
            )

    json_path.write_text(
        json.dumps(
            [
                {
                    **order.model_dump(),
                    "order_time": order.order_time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for order in orders
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    by_brand: dict[str, int] = {}
    for order in orders:
        by_brand[order.l2_tenant_id] = by_brand.get(order.l2_tenant_id, 0) + 1

    print(f"Wrote {len(orders)} orders to {csv_path}")
    print(f"Wrote {len(orders)} orders to {json_path}")
    for brand_id, count in sorted(by_brand.items()):
        print(f"  - {brand_id}: {count}")


if __name__ == "__main__":
    main()
