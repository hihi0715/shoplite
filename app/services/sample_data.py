from __future__ import annotations

import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from app.models.schemas import OrderRecord
from app.services.ingest import parse_orders_csv
from app.services.sample_generator import generate_sample_orders

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _data_candidates(filename: str) -> list[Path]:
    return [
        PROJECT_ROOT / "data" / filename,
        Path.cwd() / "data" / filename,
        Path("/var/task/data") / filename,
    ]


def resolve_sample_csv_path() -> Path | None:
    for path in _data_candidates("sample_orders.csv"):
        if path.exists():
            return path
    return None


def resolve_sample_json_path() -> Path | None:
    for path in _data_candidates("sample_orders.json"):
        if path.exists():
            return path
    return None


def _parse_order_time(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return datetime.fromisoformat(value)


def _orders_from_json(path: Path) -> list[OrderRecord]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        OrderRecord(
            l2_tenant_id=item["l2_tenant_id"],
            order_id=item["order_id"],
            user_id=item["user_id"],
            product_id=item["product_id"],
            category=item["category"],
            quantity=int(item["quantity"]),
            amount=float(item["amount"]),
            order_time=_parse_order_time(item["order_time"]),
            channel=item.get("channel", "website"),
        )
        for item in raw
    ]


@lru_cache(maxsize=1)
def load_sample_orders_from_file() -> tuple[list[OrderRecord], str]:
    json_path = resolve_sample_json_path()
    if json_path:
        return _orders_from_json(json_path), f"json:{json_path.name}"

    csv_path = resolve_sample_csv_path()
    if csv_path:
        return parse_orders_csv(csv_path.read_text(encoding="utf-8")), f"csv:{csv_path.name}"

    return generate_sample_orders(), "generated"


def get_all_sample_orders() -> list[OrderRecord]:
    orders, _ = load_sample_orders_from_file()
    return orders


def load_sample_orders_for_tenant(tenant_id: str) -> list[OrderRecord]:
    return [order for order in get_all_sample_orders() if order.l2_tenant_id == tenant_id]
