from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from threading import Lock

from app.models.schemas import EventRecord, OrderRecord

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORE_PATH = PROJECT_ROOT / "data" / ".shoplite_store.json"
VERCEL_STORE_PATH = Path("/tmp/shoplite_store.json")


def _resolve_store_path() -> Path:
    configured = os.environ.get("SHOPLITE_STORE_PATH")
    if configured:
        return Path(configured)
    if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
        return VERCEL_STORE_PATH
    return DEFAULT_STORE_PATH


def _serialize_order(order: OrderRecord) -> dict:
    data = order.model_dump()
    data["order_time"] = order.order_time.isoformat()
    return data


def _deserialize_order(data: dict) -> OrderRecord:
    payload = dict(data)
    payload["order_time"] = datetime.fromisoformat(payload["order_time"])
    return OrderRecord(**payload)


def _serialize_event(event: EventRecord) -> dict:
    data = event.model_dump()
    data["event_time"] = event.event_time.isoformat()
    return data


def _deserialize_event(data: dict) -> EventRecord:
    payload = dict(data)
    payload["event_time"] = datetime.fromisoformat(payload["event_time"])
    return EventRecord(**payload)


class DataStore:
    """Tenant-scoped store with JSON persistence for local + serverless."""

    def __init__(self) -> None:
        self._orders: dict[str, list[OrderRecord]] = {}
        self._events: dict[str, list[EventRecord]] = {}
        self._lock = Lock()
        self._path = _resolve_store_path()
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            self._orders = {
                tenant: [_deserialize_order(item) for item in items]
                for tenant, items in raw.get("orders", {}).items()
            }
            self._events = {
                tenant: [_deserialize_event(item) for item in items]
                for tenant, items in raw.get("events", {}).items()
            }
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            self._orders = {}
            self._events = {}

    def _save_to_disk(self) -> None:
        payload = {
            "orders": {
                tenant: [_serialize_order(order) for order in orders]
                for tenant, orders in self._orders.items()
            },
            "events": {
                tenant: [_serialize_event(event) for event in events]
                for tenant, events in self._events.items()
            },
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(payload), encoding="utf-8")

    def add_orders(self, tenant_id: str, orders: list[OrderRecord]) -> int:
        with self._lock:
            bucket = self._orders.setdefault(tenant_id, [])
            existing_ids = {o.order_id for o in bucket}
            new_orders = [o for o in orders if o.order_id not in existing_ids]
            bucket.extend(new_orders)
            if new_orders:
                self._save_to_disk()
            return len(new_orders)

    def add_events(self, tenant_id: str, events: list[EventRecord]) -> int:
        with self._lock:
            bucket = self._events.setdefault(tenant_id, [])
            bucket.extend(events)
            if events:
                self._save_to_disk()
            return len(events)

    def get_orders(self, tenant_id: str) -> list[OrderRecord]:
        with self._lock:
            return list(self._orders.get(tenant_id, []))

    def get_events(self, tenant_id: str) -> list[EventRecord]:
        with self._lock:
            return list(self._events.get(tenant_id, []))

    def clear_tenant(self, tenant_id: str) -> None:
        with self._lock:
            changed = tenant_id in self._orders or tenant_id in self._events
            self._orders.pop(tenant_id, None)
            self._events.pop(tenant_id, None)
            if changed:
                self._save_to_disk()

    def replace_tenant_orders(self, tenant_id: str, orders: list[OrderRecord]) -> int:
        with self._lock:
            self._orders[tenant_id] = list(orders)
            self._save_to_disk()
            return len(orders)

    def replace_all_orders(self, grouped_orders: dict[str, list[OrderRecord]]) -> dict[str, int]:
        with self._lock:
            for tenant_id in list(self._orders.keys()):
                if tenant_id in grouped_orders:
                    self._orders[tenant_id] = grouped_orders[tenant_id]
                else:
                    self._orders.pop(tenant_id, None)
            for tenant_id, orders in grouped_orders.items():
                if tenant_id not in self._orders:
                    self._orders[tenant_id] = list(orders)
            self._save_to_disk()
            return {tenant: len(orders) for tenant, orders in grouped_orders.items()}

    def list_tenants(self) -> list[str]:
        with self._lock:
            return sorted(set(self._orders) | set(self._events))


store = DataStore()
