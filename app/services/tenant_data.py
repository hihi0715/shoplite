from app.services.sample_data import load_sample_orders_for_tenant
from app.store import store


def get_tenant_orders(tenant_id: str):
    """Return uploaded orders when present, otherwise bundled sample orders."""
    uploaded = store.get_orders(tenant_id)
    if uploaded:
        return uploaded

    return load_sample_orders_for_tenant(tenant_id)
