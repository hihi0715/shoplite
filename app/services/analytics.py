from __future__ import annotations

import numpy as np

from app.models.schemas import (
    CategorySalesItem,
    CustomerSegment,
    DashboardSummary,
    TimeSeriesPoint,
    TopProductItem,
)
from app.models.schemas import OrderRecord
from app.services.kmeans import SEGMENT_LABELS, kmeans_cluster, label_clusters
from app.services.mapreduce import (
    map_category_sales,
    map_daily_sales,
    map_product_sales,
    map_user_orders,
    map_reduce,
    reduce_category_sales,
    reduce_daily_sales,
    reduce_product_sales,
    reduce_user_orders,
)


def build_dashboard_summary(tenant_id: str, orders: list[OrderRecord]) -> DashboardSummary:
    if not orders:
        return DashboardSummary(
            total_orders=0,
            total_revenue=0.0,
            unique_customers=0,
            avg_order_value=0.0,
            top_category=None,
            tenant_id=tenant_id,
        )

    total_revenue = sum(o.amount for o in orders)
    unique_customers = len({o.user_id for o in orders})
    category_totals = map_reduce(orders, map_category_sales, reduce_category_sales)
    top_category = max(category_totals, key=lambda c: category_totals[c]["revenue"])

    return DashboardSummary(
        total_orders=len(orders),
        total_revenue=round(total_revenue, 2),
        unique_customers=unique_customers,
        avg_order_value=round(total_revenue / len(orders), 2),
        top_category=top_category,
        tenant_id=tenant_id,
    )


def sales_by_category(orders: list[OrderRecord]) -> list[CategorySalesItem]:
    aggregated = map_reduce(orders, map_category_sales, reduce_category_sales)
    items = [
        CategorySalesItem(
            category=category,
            revenue=round(values["revenue"], 2),
            order_count=values["order_count"],
        )
        for category, values in aggregated.items()
    ]
    return sorted(items, key=lambda x: x.revenue, reverse=True)


def sales_over_time(orders: list[OrderRecord]) -> list[TimeSeriesPoint]:
    aggregated = map_reduce(orders, map_daily_sales, reduce_daily_sales)
    items = [
        TimeSeriesPoint(
            date=day,
            revenue=round(values["revenue"], 2),
            orders=values["orders"],
        )
        for day, values in aggregated.items()
    ]
    return sorted(items, key=lambda x: x.date)


def top_products(orders: list[OrderRecord], limit: int = 10) -> list[TopProductItem]:
    aggregated = map_reduce(orders, map_product_sales, reduce_product_sales)
    items = [
        TopProductItem(
            product_id=values["product_id"],
            category=values["category"],
            revenue=round(values["revenue"], 2),
            quantity=values["quantity"],
        )
        for _, values in aggregated.items()
    ]
    return sorted(items, key=lambda x: x.revenue, reverse=True)[:limit]


def customer_segments(orders: list[OrderRecord]) -> list[CustomerSegment]:
    if not orders:
        return []

    user_features = map_reduce(orders, map_user_orders, reduce_user_orders)
    if not user_features:
        return []

    users = list(user_features.values())
    matrix = np.array(
        [[u["recency_days"], u["frequency"], u["monetary"]] for u in users],
        dtype=float,
    )

    labels, centroids = kmeans_cluster(matrix)
    cluster_labels = label_clusters(centroids) if len(centroids) else SEGMENT_LABELS

    segments: dict[int, list[dict]] = {}
    for idx, user in enumerate(users):
        cluster_id = int(labels[idx]) if len(labels) else 0
        segments.setdefault(cluster_id, []).append(user)

    result: list[CustomerSegment] = []
    for cluster_id, members in sorted(segments.items()):
        label = cluster_labels[cluster_id] if cluster_id < len(cluster_labels) else f"客群 {cluster_id}"
        result.append(
            CustomerSegment(
                cluster_id=cluster_id,
                label=label,
                count=len(members),
                avg_recency_days=round(sum(m["recency_days"] for m in members) / len(members), 2),
                avg_frequency=round(sum(m["frequency"] for m in members) / len(members), 2),
                avg_monetary=round(sum(m["monetary"] for m in members) / len(members), 2),
            )
        )
    return result
