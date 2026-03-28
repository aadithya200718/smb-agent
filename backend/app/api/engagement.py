"""
Engagement Analytics & Management API (Feature 4).
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from app.core.database import MongoDB
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/engagement", tags=["Engagement"])


class CampaignCreateRequest(BaseModel):
    business_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    event_type: str = Field(default="promo", min_length=1)
    audience: str = Field(default="all")
    message: str = Field(..., min_length=1)
    scheduled_for: Optional[datetime] = None


@router.get("/analytics")
async def get_engagement_analytics(
    business_id: str = Query(..., description="Business identifier"),
):
    """Get engagement campaign analytics."""
    db = MongoDB.get_database()

    total_sent = await db.engagement_events.count_documents(
        {"business_id": business_id}
    )
    total_responded = await db.engagement_events.count_documents(
        {"business_id": business_id, "responded": True}
    )
    response_rate = (total_responded / total_sent * 100) if total_sent > 0 else 0

    by_type = await db.engagement_events.aggregate([
        {"$match": {"business_id": business_id}},
        {
            "$group": {
                "_id": "$event_type",
                "sent": {"$sum": 1},
                "responded": {
                    "$sum": {"$cond": ["$responded", 1, 0]}
                },
            }
        },
    ]).to_list(length=20)

    return {
        "total_sent": total_sent,
        "total_responded": total_responded,
        "response_rate": round(response_rate, 2),
        "by_type": by_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/campaigns")
async def create_campaign(body: CampaignCreateRequest):
    """Create an engagement campaign."""
    db = MongoDB.get_database()
    now = datetime.now(timezone.utc)
    campaign_id = f"cmp_{uuid.uuid4().hex[:10]}"

    scheduled_for = body.scheduled_for
    status = "scheduled" if scheduled_for and scheduled_for > now else "queued"

    doc = {
        "campaign_id": campaign_id,
        "business_id": body.business_id,
        "name": body.name,
        "event_type": body.event_type,
        "audience": body.audience,
        "message": body.message,
        "scheduled_for": scheduled_for,
        "status": status,
        "created_at": now,
    }

    await db.engagement_campaigns.insert_one(doc)

    response_doc = {**doc, "scheduled_for": scheduled_for.isoformat() if scheduled_for else None}
    response_doc["created_at"] = now.isoformat()
    return {"status": "created", "campaign": response_doc}


@router.get("/events")
async def list_engagement_events(
    business_id: str = Query(...),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(20, ge=1, le=100),
):
    """List recent engagement events."""
    db = MongoDB.get_database()

    query = {"business_id": business_id}
    if event_type:
        query["event_type"] = event_type

    cursor = db.engagement_events.find(query).sort("sent_at", -1).limit(limit)
    events = await cursor.to_list(length=limit)

    # Convert ObjectId to string
    for e in events:
        e["_id"] = str(e["_id"])

    return {"events": events, "count": len(events)}


@router.get("/scheduled")
async def get_scheduled_campaigns(
    business_id: str = Query(..., description="Business identifier"),
    limit: int = Query(20, ge=1, le=100),
):
    """List scheduled campaigns for a business."""
    db = MongoDB.get_database()
    now = datetime.now(timezone.utc)
    cursor = (
        db.engagement_campaigns
        .find(
            {
                "business_id": business_id,
                "status": "scheduled",
                "scheduled_for": {"$gte": now},
            }
        )
        .sort("scheduled_for", 1)
        .limit(limit)
    )
    campaigns = await cursor.to_list(length=limit)

    for c in campaigns:
        c["_id"] = str(c["_id"])

    return {"campaigns": campaigns, "count": len(campaigns)}


@router.post("/opt-out")
async def opt_out_user(
    phone: str = Query(..., description="Customer phone number"),
):
    """Allow a customer to opt out of proactive messages."""
    db = MongoDB.get_database()
    result = await db.users.update_one(
        {"phone": phone},
        {"$set": {"opt_out": True, "opt_out_at": datetime.now(timezone.utc)}},
    )
    if result.modified_count:
        return {"status": "opted_out", "phone": phone}
    return {"status": "not_found", "phone": phone}


@router.post("/opt-in")
async def opt_in_user(
    phone: str = Query(..., description="Customer phone number"),
):
    """Allow a customer to opt back in to proactive messages."""
    db = MongoDB.get_database()
    result = await db.users.update_one(
        {"phone": phone},
        {"$set": {"opt_out": False}, "$unset": {"opt_out_at": ""}},
    )
    if result.modified_count:
        return {"status": "opted_in", "phone": phone}
    return {"status": "not_found", "phone": phone}
