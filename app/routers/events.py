from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.dependencies import verify_api_key
from app.services.ingest import parse_events_payload
from app.store import store

router = APIRouter(prefix="/events", tags=["events"])


class EventPayload(BaseModel):
    l2_tenant_id: str = "default_brand"
    user_id: str | None = None
    anonymous_id: str | None = None
    event_name: str
    product_id: str | None = None
    event_time: datetime | None = None


class EventsBatchRequest(BaseModel):
    tenant_id: str = "default_brand"
    events: list[EventPayload] = Field(min_length=1)


@router.post("")
def ingest_events(
    payload: EventsBatchRequest,
    _: None = Depends(verify_api_key),
):
    raw_events = []
    for event in payload.events:
        item = event.model_dump()
        item["l2_tenant_id"] = payload.tenant_id
        if item.get("event_time") is None:
            item["event_time"] = datetime.utcnow().isoformat()
        else:
            item["event_time"] = item["event_time"].isoformat()
        raw_events.append(item)

    events = parse_events_payload(raw_events)
    added = store.add_events(payload.tenant_id, events)
    return {
        "tenant_id": payload.tenant_id,
        "events_added": added,
        "total_events": len(store.get_events(payload.tenant_id)),
    }
