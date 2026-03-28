"""
Order Validators.

Validates that order structures are correct.
"""
from typing import List, Dict, Any
import re

class OrderValidator:
    @staticmethod
    def validate_quantities(items: List[Dict[str, Any]]) -> bool:
        """Validate all quantities are positive integers."""
        if not items:
            return False
            
        return all(
            isinstance(item.get("quantity"), int) and item["quantity"] > 0 
            for item in items
        )
        
    @staticmethod
    def validate_ids_exist(items: List[Dict[str, Any]], menu: List[Dict[str, Any]]) -> bool:
        """Validate that requested item IDs actually exist in the current menu."""
        valid_ids = {m["item_id"] for m in menu}
        return all(item.get("item_id") in valid_ids for item in items)
        
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validates strictly Indian phone numbers format."""
        if phone.startswith("whatsapp:"):
            phone = phone[9:]
        # +91 followed by 10 digits
        pattern = re.compile(r"^\+91\d{10}$")
        return bool(pattern.match(phone))
