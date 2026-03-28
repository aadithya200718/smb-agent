"""
Menu management API endpoints.

CRUD operations for menu items with ownership verification.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import Optional

from app.core.database import MongoDB
from app.core.security import get_current_user, TokenData
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/menu", tags=["Menu"])

# Optional OAuth2 scheme — does NOT raise 401 when the header is missing
_optional_oauth2 = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


# ── Request / Response schemas ─────────────────────────────────────────

class MenuItemCreate(BaseModel):
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=1)
    description: Optional[str] = None
    available: bool = True


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = Field(default=None, gt=0)
    category: Optional[str] = None
    description: Optional[str] = None
    available: Optional[bool] = None


class AvailabilityUpdate(BaseModel):
    available: bool


# ── Endpoints ──────────────────────────────────────────────────────────

@router.get("")
async def get_menu(
    business_id: Optional[str] = Query(None, description="Filter by business"),
    token: Optional[str] = Depends(_optional_oauth2),
):
    """
    Return all menu items.  Public endpoint — if an auth token is supplied
    the business_id is inferred from it; otherwise it must be passed as a
    query parameter.
    """
    from jose import jwt, JWTError
    from app.core.config import get_settings
    settings = get_settings()

    bid = business_id
    if token and not bid:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            bid = payload.get("sub")
        except JWTError:
            pass  # ignore bad token on a public endpoint

    if not bid:
        raise HTTPException(status_code=400, detail="business_id is required")

    collection = MongoDB.get_collection("menu")
    items = await collection.find({"business_id": bid}, {"_id": 0}).to_list(length=200)
    return {"success": True, "data": items, "message": f"{len(items)} items found"}


@router.post("")
async def create_menu_item(
    body: MenuItemCreate,
    current_user: TokenData = Depends(get_current_user),
):
    """Create a new menu item for the authenticated business."""
    collection = MongoDB.get_collection("menu")
    item_id = f"item_{uuid.uuid4().hex[:10]}"

    doc = {
        "item_id": item_id,
        "business_id": current_user.sub,
        "name": body.name,
        "price": body.price,
        "category": body.category,
        "description": body.description,
        "available": body.available,
    }
    await collection.insert_one(doc)
    doc.pop("_id", None)
    logger.info("Menu item created: %s for %s", item_id, current_user.sub)
    return {"success": True, "data": doc, "message": "Menu item created"}


@router.put("/{item_id}")
async def update_menu_item(
    item_id: str,
    body: MenuItemUpdate,
    current_user: TokenData = Depends(get_current_user),
):
    """Update an existing menu item (ownership verified)."""
    collection = MongoDB.get_collection("menu")
    existing = await collection.find_one({"item_id": item_id, "business_id": current_user.sub})
    if not existing:
        raise HTTPException(status_code=404, detail="Menu item not found")

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    await collection.update_one({"item_id": item_id}, {"$set": updates})
    updated = await collection.find_one({"item_id": item_id}, {"_id": 0})
    return {"success": True, "data": updated, "message": "Menu item updated"}


@router.delete("/{item_id}")
async def delete_menu_item(
    item_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """Delete a menu item (ownership verified)."""
    collection = MongoDB.get_collection("menu")
    result = await collection.delete_one({"item_id": item_id, "business_id": current_user.sub})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Menu item not found")

    return {"success": True, "data": {"item_id": item_id}, "message": "Menu item deleted"}


@router.patch("/{item_id}/availability")
async def toggle_availability(
    item_id: str,
    body: AvailabilityUpdate,
    current_user: TokenData = Depends(get_current_user),
):
    """Toggle the availability of a menu item."""
    collection = MongoDB.get_collection("menu")
    result = await collection.update_one(
        {"item_id": item_id, "business_id": current_user.sub},
        {"$set": {"available": body.available}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Menu item not found")

    return {
        "success": True,
        "data": {"item_id": item_id, "available": body.available},
        "message": f"Item {'enabled' if body.available else 'disabled'}",
    }
