from collections import defaultdict

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.brands import BRAND_LIST
from app.dependencies import verify_api_key
from app.services.ingest import parse_orders_csv
from app.services.sample_data import (
    get_all_sample_orders,
    load_sample_orders_from_file,
    resolve_sample_csv_path,
    resolve_sample_json_path,
)
from app.services.tenant_data import get_tenant_orders
from app.store import store

router = APIRouter(prefix="/orders", tags=["orders"])


def _group_orders_by_tenant(orders: list) -> dict[str, list]:
    grouped: dict[str, list] = defaultdict(list)
    for order in orders:
        grouped[order.l2_tenant_id].append(order)
    return grouped


@router.get("/brands")
def list_brands():
    return {"brands": BRAND_LIST}


@router.get("/import-status")
def import_status():
    sample_orders, source = load_sample_orders_from_file()
    sample_grouped = _group_orders_by_tenant(sample_orders)
    store_counts = {
        brand_id: len(store.get_orders(brand_id))
        for brand_id in sample_grouped
    }
    return {
        "sample_file": {
            "csv_exists": resolve_sample_csv_path() is not None,
            "json_exists": resolve_sample_json_path() is not None,
            "source": source,
            "total_rows": len(sample_orders),
            "by_brand": {brand: len(rows) for brand, rows in sample_grouped.items()},
        },
        "store": {
            "by_brand": store_counts,
            "total_rows": sum(store_counts.values()),
        },
    }


@router.post("/upload")
async def upload_orders(
    file: UploadFile = File(...),
    tenant_id: str = Query(default="aura_beauty"),
    _: None = Depends(verify_api_key),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")

    content = (await file.read()).decode("utf-8-sig")
    try:
        orders = parse_orders_csv(content, default_tenant=tenant_id)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    grouped = _group_orders_by_tenant(orders)
    results: dict[str, int] = {}
    for tid, tenant_orders in grouped.items():
        results[tid] = store.add_orders(tid, tenant_orders)

    return {
        "tenant_id": tenant_id,
        "rows_parsed": len(orders),
        "rows_added_by_brand": results,
        "total_orders": sum(results.values()),
    }


@router.post("/load-sample")
def load_sample_data(
    tenant_id: str | None = Query(default=None),
    _: None = Depends(verify_api_key),
):
    all_orders, source = load_sample_orders_from_file()
    if not all_orders:
        raise HTTPException(status_code=500, detail="模擬訂單資料不存在，請執行 python scripts/generate_sample_data.py")

    grouped = _group_orders_by_tenant(all_orders)

    if tenant_id:
        if tenant_id not in grouped:
            raise HTTPException(status_code=404, detail=f"找不到品牌模擬資料: {tenant_id}")
        added = store.replace_tenant_orders(tenant_id, grouped[tenant_id])
        stored = len(store.get_orders(tenant_id))
        return {
            "mode": "single",
            "tenant_id": tenant_id,
            "rows_added": added,
            "rows_in_store": stored,
            "source": source,
        }

    results = store.replace_all_orders(grouped)
    stored_by_brand = {brand: len(store.get_orders(brand)) for brand in results}
    return {
        "mode": "all",
        "brands_loaded": results,
        "rows_added": sum(results.values()),
        "rows_in_store": stored_by_brand,
        "source": source,
    }


@router.get("")
def list_orders(
    tenant_id: str = Query(default="aura_beauty"),
    limit: int = Query(default=20, ge=1, le=200),
):
    orders = get_tenant_orders(tenant_id)
    return {
        "tenant_id": tenant_id,
        "total_count": len(orders),
        "count": min(limit, len(orders)),
        "orders": [o.model_dump() for o in orders[:limit]],
    }
