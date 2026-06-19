from __future__ import annotations

import numpy as np

from app.brands import get_channel_label, get_product_name
from app.models.schemas import OrderRecord
from app.services.analytics import customer_segments, sales_by_category, top_products
from app.services.kmeans import kmeans_cluster, label_clusters
from app.services.mapreduce import (
    map_channel_monthly,
    map_channel_sales,
    map_product_sales,
    map_reduce,
    map_user_orders,
    reduce_channel_monthly,
    reduce_channel_sales,
    reduce_product_sales,
    reduce_user_orders,
)


def build_products_page(orders: list[OrderRecord]) -> dict:
    if not orders:
        return {
            "summary": {
                "product_count": 0,
                "category_count": 0,
                "top_product": None,
                "total_revenue": 0,
            },
            "categories": [],
            "products": [],
        }

    categories = sales_by_category(orders)
    products_raw = top_products(orders, limit=50)
    products = [
        {
            "product_id": item.product_id,
            "product_name": get_product_name(item.product_id),
            "category": item.category,
            "revenue": item.revenue,
            "quantity": item.quantity,
            "avg_price": round(item.revenue / item.quantity, 2) if item.quantity else 0,
        }
        for item in products_raw
    ]

    return {
        "summary": {
            "product_count": len(products),
            "category_count": len(categories),
            "top_product": products[0]["product_name"] if products else None,
            "total_revenue": round(sum(p["revenue"] for p in products), 2),
        },
        "categories": [c.model_dump() for c in categories],
        "products": products,
    }


def build_customers_page(orders: list[OrderRecord], customer_limit: int = 20) -> dict:
    if not orders:
        return {
            "summary": {
                "total_customers": 0,
                "repeat_rate": 0,
                "avg_frequency": 0,
                "avg_monetary": 0,
            },
            "segments": [],
            "customers": [],
        }

    user_features = map_reduce(orders, map_user_orders, reduce_user_orders)
    users = list(user_features.values())
    matrix = np.array(
        [[u["recency_days"], u["frequency"], u["monetary"]] for u in users],
        dtype=float,
    )
    labels, centroids = kmeans_cluster(matrix)
    cluster_labels = label_clusters(centroids) if len(centroids) else []

    customers = []
    repeat_customers = 0
    for idx, user in enumerate(users):
        cluster_id = int(labels[idx]) if len(labels) else 0
        segment = cluster_labels[cluster_id] if cluster_id < len(cluster_labels) else f"客群 {cluster_id}"
        if user["frequency"] >= 2:
            repeat_customers += 1
        customers.append(
            {
                "user_id": user["user_id"],
                "segment": segment,
                "recency_days": user["recency_days"],
                "frequency": user["frequency"],
                "monetary": round(user["monetary"], 2),
            }
        )

    customers.sort(key=lambda item: item["monetary"], reverse=True)
    total = len(users)

    return {
        "summary": {
            "total_customers": total,
            "repeat_rate": round(repeat_customers / total * 100, 1) if total else 0,
            "avg_frequency": round(sum(u["frequency"] for u in users) / total, 2) if total else 0,
            "avg_monetary": round(sum(u["monetary"] for u in users) / total, 2) if total else 0,
        },
        "segments": [s.model_dump() for s in customer_segments(orders)],
        "customers": customers[:customer_limit],
    }


def build_channels_page(orders: list[OrderRecord]) -> dict:
    if not orders:
        return {
            "summary": {
                "channel_count": 0,
                "top_channel": None,
                "total_revenue": 0,
            },
            "channels": [],
            "trends": [],
        }

    channel_data = map_reduce(orders, map_channel_sales, reduce_channel_sales)
    channels = []
    for channel, values in channel_data.items():
        orders_count = values["orders"]
        revenue = round(values["revenue"], 2)
        channels.append(
            {
                "channel": channel,
                "channel_label": get_channel_label(channel),
                "revenue": revenue,
                "orders": orders_count,
                "avg_order_value": round(revenue / orders_count, 2) if orders_count else 0,
            }
        )
    channels.sort(key=lambda item: item["revenue"], reverse=True)

    monthly_data = map_reduce(orders, map_channel_monthly, reduce_channel_monthly)
    trends = [
        {
            "channel": values["channel"],
            "channel_label": get_channel_label(values["channel"]),
            "month": values["month"],
            "revenue": round(values["revenue"], 2),
            "orders": values["orders"],
        }
        for _, values in monthly_data.items()
    ]
    trends.sort(key=lambda item: (item["month"], item["channel"]))

    return {
        "summary": {
            "channel_count": len(channels),
            "top_channel": channels[0]["channel_label"] if channels else None,
            "total_revenue": round(sum(c["revenue"] for c in channels), 2),
        },
        "channels": channels,
        "trends": trends,
    }
