"""
Business profile and chat-history API endpoints.
"""

import math
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.database import MongoDB
from app.core.security import get_current_user, TokenData
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/business", tags=["Business"])


# ── Request / Response schemas ─────────────────────────────────────────

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    timings: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None


# ── Endpoints ──────────────────────────────────────────────────────────

@router.get("/profile")
async def get_profile(current_user: TokenData = Depends(get_current_user)):
    """Return the business profile for the authenticated user."""
    collection = MongoDB.get_collection("businesses")
    business = await collection.find_one(
        {"business_id": current_user.sub}, {"_id": 0, "owner_password": 0}
    )
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    return {"success": True, "data": business, "message": "Profile retrieved"}


@router.put("/profile")
async def update_profile(
    body: ProfileUpdate,
    current_user: TokenData = Depends(get_current_user),
):
    """Update the business profile."""
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    collection = MongoDB.get_collection("businesses")
    result = await collection.update_one(
        {"business_id": current_user.sub}, {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Business not found")

    updated = await collection.find_one(
        {"business_id": current_user.sub}, {"_id": 0, "owner_password": 0}
    )
    return {"success": True, "data": updated, "message": "Profile updated"}


@router.get("/chats")
async def list_chats(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user),
):
    """Return paginated chat sessions for the business."""
    collection = MongoDB.get_collection("chats")
    query = {"business_id": current_user.sub}

    total = await collection.count_documents(query)
    skip = (page - 1) * limit
    chats = (
        await collection.find(query, {"_id": 0, "messages": 0})
        .sort("updated_at", -1)
        .skip(skip)
        .limit(limit)
        .to_list(length=limit)
    )

    return {
        "success": True,
        "data": chats,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": math.ceil(total / limit) if total else 0,
        },
    }


@router.get("/chats/{customer_phone}")
async def get_chat(
    customer_phone: str,
    current_user: TokenData = Depends(get_current_user),
):
    """Return the full conversation with a specific customer."""
    collection = MongoDB.get_collection("chats")
    chat = await collection.find_one(
        {"business_id": current_user.sub, "customer_phone": customer_phone},
        {"_id": 0},
    )
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    return {"success": True, "data": chat, "message": "Chat retrieved"}
