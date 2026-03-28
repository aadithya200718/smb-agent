"""
Petpooja POS Integration.

Real-time menu sync, stock validation, order creation, and stock deduction
via Petpooja REST API. Includes a fallback mock mode when credentials
are not configured (for demos and testing).
"""

import httpx
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.core.config import get_settings
from app.utils.logger import get_logger
from app.utils.circuit_breaker import CircuitBreaker

logger = get_logger(__name__)
settings = get_settings()

# Circuit breaker for Petpooja API calls
_petpooja_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)


class PetpoojaClient:
    """
    Client for the Petpooja POS API.
    
    Provides:
      - Real-time menu sync with stock status
      - Live inventory validation before order
      - Auto-create orders in POS
      - Stock deduction on order confirmation
      - Price sync (prevent stale pricing)
      
    Falls back to mock mode when PETPOOJA_API_TOKEN is not set.
    """

    def __init__(self):
        self.api_token = getattr(settings, "PETPOOJA_API_TOKEN", None) or ""
        self.restaurant_id = getattr(settings, "PETPOOJA_RESTAURANT_ID", None) or ""
        self.base_url = "https://api.petpooja.com/v2"
        self.mock_mode = not bool(self.api_token)

        if self.mock_mode:
            logger.warning("Petpooja credentials missing — running in MOCK mode.")
        else:
            logger.info("PetpoojaClient initialized for restaurant %s", self.restaurant_id)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "X-Restaurant-ID": self.restaurant_id,
        }

    # ── Mock Data ─────────────────────────────────────────────────────

    _MOCK_MENU: List[Dict[str, Any]] = [
        {
            "item_id": "PP001",
            "name": "Veg Biryani",
            "price": 149.0,
            "category": "Mains",
            "description": "Aromatic basmati rice with mixed vegetables and spices.",
            "stock": 50,
            "available": True,
            "variants": [],
        },
        {
            "item_id": "PP002",
            "name": "Paneer Butter Masala",
            "price": 179.0,
            "category": "Mains",
            "description": "Cottage cheese cubes in rich tomato gravy.",
            "stock": 30,
            "available": True,
            "variants": [],
        },
        {
            "item_id": "PP003",
            "name": "Chicken Biryani",
            "price": 199.0,
            "category": "Mains",
            "description": "Fragrant rice layered with tender chicken.",
            "stock": 40,
            "available": True,
            "variants": [],
        },
        {
            "item_id": "PP004",
            "name": "Masala Dosa",
            "price": 89.0,
            "category": "Starters",
            "description": "Crispy crepe with spiced potato filling.",
            "stock": 25,
            "available": True,
            "variants": [],
        },
        {
            "item_id": "PP005",
            "name": "Chole Bhature",
            "price": 129.0,
            "category": "Mains",
            "description": "Spicy chickpea curry with fried bread.",
            "stock": 0,
            "available": False,
            "variants": [],
        },
        {
            "item_id": "PP006",
            "name": "Mango Lassi",
            "price": 69.0,
            "category": "Beverages",
            "description": "Refreshing yogurt-based mango drink.",
            "stock": 100,
            "available": True,
            "variants": [{"name": "Regular", "price": 69.0}, {"name": "Large", "price": 99.0}],
        },
    ]

    _mock_stock: Dict[str, int] = {}

    def _init_mock_stock(self):
        if not self._mock_stock:
            for item in self._MOCK_MENU:
                self._mock_stock[item["item_id"]] = item["stock"]

    # ── Menu Sync ─────────────────────────────────────────────────────

    @_petpooja_breaker
    async def fetch_menu(self) -> List[Dict[str, Any]]:
        """
        Fetch the full menu from Petpooja POS.
        Returns list of menu items with stock status and pricing.
        """
        if self.mock_mode:
            self._init_mock_stock()
            # Update availability based on mock stock
            menu = []
            for item in self._MOCK_MENU:
                item_copy = dict(item)
                item_copy["stock"] = self._mock_stock.get(item["item_id"], item["stock"])
                item_copy["available"] = item_copy["stock"] > 0
                menu.append(item_copy)
            logger.info("Petpooja MOCK: returning %d menu items", len(menu))
            return menu

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/restaurants/{self.restaurant_id}/menu",
                    headers=self._headers(),
                    timeout=10.0,
                )
                resp.raise_for_status()
                data = resp.json()
                items = data.get("items", [])
                logger.info("Petpooja: fetched %d menu items", len(items))
                return items
        except Exception as e:
            logger.error("Petpooja menu fetch failed: %s", e)
            raise

    # ── Stock Validation ──────────────────────────────────────────────

    @_petpooja_breaker
    async def check_stock(self, item_id: str, quantity: int = 1) -> Dict[str, Any]:
        """
        Check if an item has sufficient stock in the POS.
        
        Returns:
            {"available": bool, "current_stock": int, "item_id": str}
        """
        if self.mock_mode:
            self._init_mock_stock()
            current = self._mock_stock.get(item_id, 0)
            available = current >= quantity
            result = {
                "available": available,
                "current_stock": current,
                "item_id": item_id,
            }
            if not available:
                logger.warning("Petpooja MOCK: Item %s out of stock (need %d, have %d)",
                               item_id, quantity, current)
            return result

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/restaurants/{self.restaurant_id}/stock/{item_id}",
                    headers=self._headers(),
                    timeout=10.0,
                )
                resp.raise_for_status()
                data = resp.json()
                current_stock = data.get("stock", 0)
                return {
                    "available": current_stock >= quantity,
                    "current_stock": current_stock,
                    "item_id": item_id,
                }
        except Exception as e:
            logger.error("Petpooja stock check failed for %s: %s", item_id, e)
            raise

    # ── Get Current Price ─────────────────────────────────────────────

    @_petpooja_breaker
    async def get_item_price(self, item_id: str) -> Optional[float]:
        """
        Get the latest price for an item from the POS (prevents stale pricing).
        """
        if self.mock_mode:
            self._init_mock_stock()
            for item in self._MOCK_MENU:
                if item["item_id"] == item_id:
                    return item["price"]
            return None

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/restaurants/{self.restaurant_id}/items/{item_id}",
                    headers=self._headers(),
                    timeout=10.0,
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("price")
        except Exception as e:
            logger.error("Petpooja price fetch failed for %s: %s", item_id, e)
            raise

    # ── Create Order in POS ───────────────────────────────────────────

    @_petpooja_breaker
    async def create_pos_order(
        self,
        order_id: str,
        items: List[Dict[str, Any]],
        customer_phone: str,
    ) -> Dict[str, Any]:
        """
        Push an order to the Petpooja POS system.
        
        Returns the POS order confirmation with POS-specific order ID.
        """
        if self.mock_mode:
            self._init_mock_stock()
            pos_order_id = f"POS-{order_id}"
            logger.info("Petpooja MOCK: created POS order %s", pos_order_id)
            return {
                "pos_order_id": pos_order_id,
                "status": "accepted",
                "estimated_time_minutes": 20,
            }

        try:
            payload = {
                "external_order_id": order_id,
                "items": [
                    {
                        "item_id": item["item_id"],
                        "quantity": item["quantity"],
                        "unit_price": item["unit_price"],
                        "notes": item.get("notes", ""),
                    }
                    for item in items
                ],
                "customer": {"phone": customer_phone},
                "order_type": "takeaway",
            }

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/restaurants/{self.restaurant_id}/orders",
                    headers=self._headers(),
                    json=payload,
                    timeout=15.0,
                )
                resp.raise_for_status()
                data = resp.json()
                logger.info("Petpooja: POS order created — %s", data.get("pos_order_id"))
                return data
        except Exception as e:
            logger.error("Petpooja order creation failed: %s", e)
            raise

    # ── Stock Deduction ───────────────────────────────────────────────

    @_petpooja_breaker
    async def deduct_stock(self, item_id: str, quantity: int) -> bool:
        """
        Deduct stock in POS after order confirmation.
        """
        if self.mock_mode:
            self._init_mock_stock()
            current = self._mock_stock.get(item_id, 0)
            if current >= quantity:
                self._mock_stock[item_id] = current - quantity
                logger.info("Petpooja MOCK: deducted %d of %s (remaining: %d)",
                           quantity, item_id, self._mock_stock[item_id])
                return True
            else:
                logger.warning("Petpooja MOCK: cannot deduct %d of %s (only %d left)",
                             quantity, item_id, current)
                return False

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/restaurants/{self.restaurant_id}/stock/deduct",
                    headers=self._headers(),
                    json={"item_id": item_id, "quantity": quantity},
                    timeout=10.0,
                )
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error("Petpooja stock deduction failed for %s: %s", item_id, e)
            return False

    # ── Suggest Alternatives ──────────────────────────────────────────

    async def suggest_alternatives(self, item_id: str) -> List[Dict[str, Any]]:
        """
        When an item is out of stock, suggest similar available items
        from the same category.
        """
        menu = await self.fetch_menu()

        # Find the out-of-stock item's category
        target_category = None
        for item in menu:
            if item["item_id"] == item_id:
                target_category = item.get("category")
                break

        if not target_category:
            return []

        # Return available items from the same category
        alternatives = [
            item for item in menu
            if item.get("category") == target_category
            and item.get("available", False)
            and item["item_id"] != item_id
        ]

        logger.info("Petpooja: suggesting %d alternatives for %s", len(alternatives), item_id)
        return alternatives[:3]


# Singleton instance
petpooja_client = PetpoojaClient()
