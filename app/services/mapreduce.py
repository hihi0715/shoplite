from __future__ import annotations

import multiprocessing
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Callable, Hashable, TypeVar

from app.config import get_settings

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


def _chunk_data(data: list, num_chunks: int) -> list[list]:
    if not data:
        return []
    chunk_size = max(1, len(data) // num_chunks + (1 if len(data) % num_chunks else 0))
    return [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]


def map_reduce(
    items: list,
    mapper: Callable[[list], list[tuple[K, V]]],
    reducer: Callable[[K, list[V]], tuple[K, object]],
    num_workers: int | None = None,
) -> dict[K, object]:
    """MapReduce-style aggregation with thread or process workers."""
    if not items:
        return {}

    settings = get_settings()
    workers = num_workers or settings.mapreduce_workers
    chunks = _chunk_data(items, workers)

    mapped: list[tuple[K, V]] = []
    if settings.use_multiprocessing and len(chunks) > 1:
        with multiprocessing.Pool(processes=min(workers, len(chunks))) as pool:
            for partial in pool.map(mapper, chunks):
                mapped.extend(partial)
    else:
        with ThreadPoolExecutor(max_workers=min(workers, len(chunks))) as executor:
            for partial in executor.map(mapper, chunks):
                mapped.extend(partial)

    grouped: dict[K, list[V]] = defaultdict(list)
    for key, value in mapped:
        grouped[key].append(value)

    return {key: reducer(key, values)[1] for key, values in grouped.items()}


def map_category_sales(orders_chunk: list) -> list[tuple[str, tuple[float, int]]]:
    results: list[tuple[str, tuple[float, int]]] = []
    for order in orders_chunk:
        results.append((order.category, (order.amount, 1)))
    return results


def reduce_category_sales(category: str, values: list[tuple[float, int]]) -> tuple[str, dict]:
    revenue = sum(v[0] for v in values)
    count = sum(v[1] for v in values)
    return category, {"revenue": revenue, "order_count": count}


def map_daily_sales(orders_chunk: list) -> list[tuple[str, tuple[float, int]]]:
    results: list[tuple[str, tuple[float, int]]] = []
    for order in orders_chunk:
        day = order.order_time.strftime("%Y-%m-%d")
        results.append((day, (order.amount, 1)))
    return results


def reduce_daily_sales(day: str, values: list[tuple[float, int]]) -> tuple[str, dict]:
    revenue = sum(v[0] for v in values)
    count = sum(v[1] for v in values)
    return day, {"revenue": revenue, "orders": count}


def map_product_sales(orders_chunk: list) -> list[tuple[str, tuple[str, float, int]]]:
    results: list[tuple[str, tuple[str, float, int]]] = []
    for order in orders_chunk:
        results.append((order.product_id, (order.category, order.amount, order.quantity)))
    return results


def reduce_product_sales(
    product_id: str, values: list[tuple[str, float, int]]
) -> tuple[str, dict]:
    category = values[0][0]
    revenue = sum(v[1] for v in values)
    quantity = sum(v[2] for v in values)
    return product_id, {
        "product_id": product_id,
        "category": category,
        "revenue": revenue,
        "quantity": quantity,
    }


def map_user_orders(orders_chunk: list) -> list[tuple[str, tuple[datetime, float]]]:
    results: list[tuple[str, tuple[datetime, float]]] = []
    for order in orders_chunk:
        results.append((order.user_id, (order.order_time, order.amount)))
    return results


def reduce_user_orders(
    user_id: str, values: list[tuple[datetime, float]]
) -> tuple[str, dict]:
    times = [v[0] for v in values]
    amounts = [v[1] for v in values]
    latest = max(times)
    recency_days = (datetime.utcnow() - latest).days
    return user_id, {
        "user_id": user_id,
        "recency_days": recency_days,
        "frequency": len(values),
        "monetary": sum(amounts),
    }
