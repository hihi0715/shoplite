from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Iterable

from app.models.schemas import EventRecord, OrderRecord

REQUIRED_ORDER_COLUMNS = {
    "order_id",
    "user_id",
    "product_id",
    "category",
    "quantity",
    "amount",
    "order_time",
}

OPTIONAL_ORDER_COLUMNS = {"l2_tenant_id", "channel"}


def _parse_datetime(value: str) -> datetime:
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return datetime.fromisoformat(value.strip())


def parse_orders_csv(
    content: str,
    default_tenant: str = "default_brand",
) -> list[OrderRecord]:
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise ValueError("CSV has no header row")

    headers = {h.strip().lower() for h in reader.fieldnames}
    missing = REQUIRED_ORDER_COLUMNS - headers
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    orders: list[OrderRecord] = []
    for row in reader:
        normalized = {k.strip().lower(): (v or "").strip() for k, v in row.items()}
        orders.append(
            OrderRecord(
                l2_tenant_id=normalized.get("l2_tenant_id") or default_tenant,
                order_id=normalized["order_id"],
                user_id=normalized["user_id"],
                product_id=normalized["product_id"],
                category=normalized["category"],
                quantity=int(float(normalized["quantity"])),
                amount=float(normalized["amount"]),
                order_time=_parse_datetime(normalized["order_time"]),
                channel=normalized.get("channel") or "website",
            )
        )
    return orders


def parse_events_payload(events: Iterable[dict]) -> list[EventRecord]:
    parsed: list[EventRecord] = []
    for item in events:
        event_time = item["event_time"]
        if isinstance(event_time, str):
            event_time = _parse_datetime(event_time)
        parsed.append(
            EventRecord(
                l2_tenant_id=item.get("l2_tenant_id", "default_brand"),
                user_id=item.get("user_id"),
                anonymous_id=item.get("anonymous_id"),
                event_name=item["event_name"],
                product_id=item.get("product_id"),
                event_time=event_time,
            )
        )
    return parsed
