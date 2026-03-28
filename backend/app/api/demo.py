"""
Demo API — synchronous endpoint for the live demo video.

Bypasses Twilio entirely. The frontend sends a message, the agent
processes it synchronously, and the full trace_log + response are
returned in one JSON payload so the split-screen UI can render them.

Also includes a seed endpoint to populate 25 realistic QSR menu items.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.agent.graph import run_agent
from app.core.database import MongoDB
from app.models.menu import MenuItem
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/demo", tags=["Demo"])


# ── Request / Response schemas ────────────────────────────────────────

class DemoChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    phone_number: str = Field(default="+919876543210")


class DemoChatResponse(BaseModel):
    reply: str
    trace_log: List[Dict[str, Any]]
    intent: str | None = None
    retry_count: int = 0
    validation_passed: bool = True


# ── POST /demo/chat ──────────────────────────────────────────────────

@router.post("/chat", response_model=DemoChatResponse)
async def demo_chat(req: DemoChatRequest):
    """
    Send a message to the AI agent and get the response + trace log
    synchronously. Designed for the demo video's split-screen UI.
    """
    logger.info("DEMO CHAT — message: %s", req.message[:80])

    final_state = await run_agent(
        message=req.message,
        user_phone=req.phone_number,
        business_id="BIZ001",
    )

    validation = final_state.get("validation_result") or {}

    return DemoChatResponse(
        reply=final_state.get("response") or "Sorry, I couldn't process that.",
        trace_log=final_state.get("trace_log", []),
        intent=final_state.get("current_intent"),
        retry_count=final_state.get("retry_count", 0),
        validation_passed=validation.get("passed", True),
    )


# ── GET /demo/menu ───────────────────────────────────────────────────

@router.get("/menu")
async def get_demo_menu():
    """Return the current menu items for BIZ001."""
    try:
        db = MongoDB.get_database()
        cursor = db.menu_items.find({"business_id": "BIZ001"})
        docs = await cursor.to_list(length=100)
        # Remove MongoDB _id for JSON serialization
        for d in docs:
            d.pop("_id", None)
        return {"items": docs, "count": len(docs)}
    except Exception as e:
        logger.error("get_demo_menu failed: %s", e)
        return {"items": [], "count": 0}


# ── POST /demo/seed-menu ────────────────────────────────────────────

SEED_MENU: List[Dict[str, Any]] = [
    # ── Starters ──────────────────────────────────────────────────
    {"item_id": "M01", "name": "Paneer Tikka", "price": 220, "category": "Starters",
     "description": "Marinated cottage cheese cubes grilled in tandoor with bell peppers"},
    {"item_id": "M02", "name": "Chicken 65", "price": 250, "category": "Starters",
     "description": "Spicy deep-fried chicken bites tossed with curry leaves & chillies"},
    {"item_id": "M03", "name": "Veg Manchurian", "price": 180, "category": "Starters",
     "description": "Crispy vegetable balls in tangy Indo-Chinese Manchurian sauce"},
    {"item_id": "M04", "name": "Fish Amritsari", "price": 280, "category": "Starters",
     "description": "Batter-fried fish fillets seasoned with ajwain and chaat masala"},
    {"item_id": "M05", "name": "Masala Papad", "price": 60, "category": "Starters",
     "description": "Roasted papad topped with onion, tomato, and green chutney"},

    # ── Mains (Rice) ─────────────────────────────────────────────
    {"item_id": "M06", "name": "Chicken Biryani", "price": 280, "category": "Mains",
     "description": "Fragrant basmati rice layered with tender chicken, saffron & dum cooked"},
    {"item_id": "M07", "name": "Veg Biryani", "price": 200, "category": "Mains",
     "description": "Aromatic rice with seasonal vegetables, mint, and whole spices"},
    {"item_id": "M08", "name": "Mutton Biryani", "price": 350, "category": "Mains",
     "description": "Slow-cooked goat meat biryani with caramelised onions & rose water"},
    {"item_id": "M09", "name": "Egg Fried Rice", "price": 160, "category": "Mains",
     "description": "Wok-tossed basmati rice with scrambled eggs, vegetables & soy sauce"},

    # ── Mains (Curries) ─────────────────────────────────────────
    {"item_id": "M10", "name": "Paneer Butter Masala", "price": 240, "category": "Mains",
     "description": "Cottage cheese in rich tomato-cashew gravy with a hint of cream"},
    {"item_id": "M11", "name": "Butter Chicken", "price": 280, "category": "Mains",
     "description": "Tandoori chicken simmered in velvety tomato-butter gravy"},
    {"item_id": "M12", "name": "Dal Makhani", "price": 200, "category": "Mains",
     "description": "Black lentils slow-cooked overnight with butter and cream"},
    {"item_id": "M13", "name": "Chole Bhature", "price": 150, "category": "Mains",
     "description": "Spiced chickpea curry served with fluffy deep-fried bread"},
    {"item_id": "M14", "name": "Kadai Chicken", "price": 260, "category": "Mains",
     "description": "Chicken cooked with capsicum in a spicy kadai masala"},

    # ── Breads ───────────────────────────────────────────────────
    {"item_id": "M15", "name": "Butter Naan", "price": 50, "category": "Breads",
     "description": "Soft leavened bread brushed with melted butter from tandoor"},
    {"item_id": "M16", "name": "Garlic Naan", "price": 60, "category": "Breads",
     "description": "Naan topped with minced garlic and coriander"},
    {"item_id": "M17", "name": "Tandoori Roti", "price": 30, "category": "Breads",
     "description": "Whole wheat flatbread baked crisp in clay oven"},
    {"item_id": "M18", "name": "Laccha Paratha", "price": 50, "category": "Breads",
     "description": "Layered flaky whole wheat paratha cooked with ghee"},

    # ── South Indian ─────────────────────────────────────────────
    {"item_id": "M19", "name": "Masala Dosa", "price": 120, "category": "South Indian",
     "description": "Crispy rice crepe filled with spiced potato, served with sambar & chutney"},
    {"item_id": "M20", "name": "Idli Sambar", "price": 80, "category": "South Indian",
     "description": "Steamed rice cakes served with lentil sambar and coconut chutney"},

    # ── Beverages ────────────────────────────────────────────────
    {"item_id": "M21", "name": "Masala Chai", "price": 40, "category": "Beverages",
     "description": "Traditional Indian spiced tea brewed with ginger and cardamom"},
    {"item_id": "M22", "name": "Mango Lassi", "price": 90, "category": "Beverages",
     "description": "Chilled yogurt smoothie blended with Alphonso mango pulp"},
    {"item_id": "M23", "name": "Cold Coffee", "price": 120, "category": "Beverages",
     "description": "Blended iced coffee with milk, cream, and chocolate drizzle"},

    # ── Desserts ─────────────────────────────────────────────────
    {"item_id": "M24", "name": "Gulab Jamun", "price": 80, "category": "Desserts",
     "description": "Soft milk-solid dumplings soaked in rose-cardamom sugar syrup"},
    {"item_id": "M25", "name": "Rasmalai", "price": 100, "category": "Desserts",
     "description": "Flattened cottage cheese balls in chilled saffron milk with pistachios"},
]


@router.post("/seed-menu")
async def seed_demo_menu():
    """
    Drop existing BIZ001 menu and insert 25 curated QSR items.
    Call this once before recording the demo video.
    """
    try:
        db = MongoDB.get_database()

        # Clear existing menu for BIZ001
        result = await db.menu_items.delete_many({"business_id": "BIZ001"})
        logger.info("Cleared %d old menu items", result.deleted_count)

        # Build MenuItem objects
        items = []
        for seed in SEED_MENU:
            item = MenuItem(
                item_id=seed["item_id"],
                business_id="BIZ001",
                name=seed["name"],
                price=seed["price"],
                category=seed["category"],
                description=seed["description"],
                available=True,
            )
            items.append(item.model_dump())

        await db.menu_items.insert_many(items)
        logger.info("Seeded %d menu items for BIZ001", len(items))

        return {
            "status": "success",
            "message": f"Seeded {len(items)} menu items",
            "items": [{"name": s["name"], "price": s["price"], "category": s["category"]} for s in SEED_MENU],
        }
    except Exception as e:
        logger.error("seed_demo_menu failed: %s", e)
        return {"status": "error", "message": str(e)}
