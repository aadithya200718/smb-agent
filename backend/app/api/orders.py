"""
Order management API endpoints.

List, view, and update order statuses with pagination and filtering.
"""

import math
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional

from app.core.database import MongoDB
from app.core.security import get_current_user, TokenData
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/orders", tags=["Orders"])


# ── Request / Response schemas ─────────────────────────────────────────

class StatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|confirmed|completed|cancelled)$")


# ── Endpoints ──────────────────────────────────────────────────────────

@router.get("/stats")
async def order_stats(current_user: TokenData = Depends(get_current_user)):
    """
    Aggregate order statistics for the authenticated business.
    NOTE: Defined before /{order_id} to avoid route collision.
    """
    collection = MongoDB.get_collection("orders")
    bid = current_user.sub

    pipeline = [
        {"$match": {"business_id": bid}},
        {
            "$group": {
                "_id": None,
                "total_orders": {"$sum": 1},
                "total_revenue": {
                    "$sum": {
                        "$reduce": {
                            "input": "$items",
                            "initialValue": 0,
                            "in": {
                                "$add": [
                                    "$$value",
                                    {"$multiply": ["$$this.quantity", "$$this.unit_price"]},
                                ]
                            },
                        }
                    }
                },
                "pending_orders": {
                    "$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}
                },
            }
        },
    ]
    results = await collection.aggregate(pipeline).to_list(length=1)
    data = results[0] if results else {"total_orders": 0, "total_revenue": 0, "pending_orders": 0}
    data.pop("_id", None)
    return {"success": True, "data": data, "message": "Order stats retrieved"}


@router.get("")
async def list_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    date_from: Optional[str] = Query(None, description="ISO date YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="ISO date YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user),
):
    """Return paginated orders for the authenticated business."""
    collection = MongoDB.get_collection("orders")
    query: dict = {"business_id": current_user.sub}

    if status_filter:
        query["status"] = status_filter
    if date_from:
        query.setdefault("created_at", {})["$gte"] = datetime.fromisoformat(date_from).replace(
            tzinfo=timezone.utc
        )
    if date_to:
        query.setdefault("created_at", {})["$lte"] = (
            datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc) + timedelta(days=1)
        )

    total = await collection.count_documents(query)
    skip = (page - 1) * limit
    orders = (
        await collection.find(query, {"_id": 0})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
        .to_list(length=limit)
    )

    return {
        "success": True,
        "data": orders,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": math.ceil(total / limit) if total else 0,
        },
    }


@router.get("/{order_id}")
async def get_order(
    order_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """Return a single order (ownership verified)."""
    collection = MongoDB.get_collection("orders")
    order = await collection.find_one(
        {"order_id": order_id, "business_id": current_user.sub}, {"_id": 0}
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return {"success": True, "data": order, "message": "Order retrieved"}


@router.put("/{order_id}/status")
async def update_order_status(
    order_id: str,
    body: StatusUpdate,
    current_user: TokenData = Depends(get_current_user),
):
    """Update the status of an order (ownership verified)."""
    collection = MongoDB.get_collection("orders")
    result = await collection.update_one(
        {"order_id": order_id, "business_id": current_user.sub},
        {"$set": {"status": body.status}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")

    logger.info("Order %s status → %s", order_id, body.status)
    return {
        "success": True,
        "data": {"order_id": order_id, "status": body.status},
        "message": f"Order status updated to {body.status}",
    }
