from fastapi import APIRouter, Query

from app.services.analytics import (
    build_dashboard_summary,
    customer_segments,
    sales_by_category,
    sales_over_time,
    top_products,
)
from app.services.page_analytics import (
    build_channels_page,
    build_customers_page,
    build_products_page,
)
from app.services.tenant_data import get_tenant_orders

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
def dashboard(tenant_id: str = Query(default="aura_beauty")):
    orders = get_tenant_orders(tenant_id)
    return build_dashboard_summary(tenant_id, orders)


@router.get("/sales-by-category")
def category_sales(tenant_id: str = Query(default="aura_beauty")):
    orders = get_tenant_orders(tenant_id)
    return {
        "tenant_id": tenant_id,
        "items": [item.model_dump() for item in sales_by_category(orders)],
    }


@router.get("/sales-over-time")
def time_series(tenant_id: str = Query(default="aura_beauty")):
    orders = get_tenant_orders(tenant_id)
    return {
        "tenant_id": tenant_id,
        "items": [item.model_dump() for item in sales_over_time(orders)],
    }


@router.get("/top-products")
def products(tenant_id: str = Query(default="aura_beauty"), limit: int = Query(default=10, ge=1, le=50)):
    orders = get_tenant_orders(tenant_id)
    return {
        "tenant_id": tenant_id,
        "items": [item.model_dump() for item in top_products(orders, limit=limit)],
    }


@router.get("/customer-segments")
def segments(tenant_id: str = Query(default="aura_beauty")):
    orders = get_tenant_orders(tenant_id)
    return {
        "tenant_id": tenant_id,
        "items": [item.model_dump() for item in customer_segments(orders)],
    }


@router.get("/tenants")
def tenants():
    from app.store import store

    return {"tenants": store.list_tenants()}


@router.get("/pages/products")
def products_page(tenant_id: str = Query(default="aura_beauty")):
    orders = get_tenant_orders(tenant_id)
    return {"tenant_id": tenant_id, **build_products_page(orders)}


@router.get("/pages/customers")
def customers_page(
    tenant_id: str = Query(default="aura_beauty"),
    limit: int = Query(default=20, ge=1, le=100),
):
    orders = get_tenant_orders(tenant_id)
    return {"tenant_id": tenant_id, **build_customers_page(orders, customer_limit=limit)}


@router.get("/pages/channels")
def channels_page(tenant_id: str = Query(default="aura_beauty")):
    orders = get_tenant_orders(tenant_id)
    return {"tenant_id": tenant_id, **build_channels_page(orders)}
