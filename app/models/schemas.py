from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class OrderRecord(BaseModel):
    l2_tenant_id: str = "default_brand"
    order_id: str
    user_id: str
    product_id: str
    category: str
    quantity: int = Field(ge=1)
    amount: float = Field(ge=0)
    order_time: datetime
    channel: str = "website"


class EventRecord(BaseModel):
    l2_tenant_id: str = "default_brand"
    user_id: str | None = None
    anonymous_id: str | None = None
    event_name: str
    product_id: str | None = None
    event_time: datetime


class DashboardSummary(BaseModel):
    total_orders: int
    total_revenue: float
    unique_customers: int
    avg_order_value: float
    top_category: str | None
    tenant_id: str


class CategorySalesItem(BaseModel):
    category: str
    revenue: float
    order_count: int


class TimeSeriesPoint(BaseModel):
    date: str
    revenue: float
    orders: int


class TopProductItem(BaseModel):
    product_id: str
    category: str
    revenue: float
    quantity: int


class CustomerSegment(BaseModel):
    cluster_id: int
    label: str
    count: int
    avg_recency_days: float
    avg_frequency: float
    avg_monetary: float


class AnalyticsResponse(BaseModel):
    tenant_id: str
    data: list[Any]
