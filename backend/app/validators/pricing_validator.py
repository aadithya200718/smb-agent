"""
Pricing Validators.

Ensures math and repricing matches POS truth to prevent stale prices.
"""

from typing import List, Dict, Any

class PricingValidator:
    
    @staticmethod
    def validate_total_matches(items: List[Dict[str, Any]], calculated_total: float) -> bool:
        """Ensure the total equals the sum of quantity * unit_price."""
        expected_total = sum(i.get("quantity", 1) * i.get("unit_price", 0.0) for i in items)
        
        # Floating point check
        return abs(expected_total - calculated_total) < 0.01

    @staticmethod
    def apply_valid_discount(total: float, code: str) -> float:
        """Validates and applies a discount. Stub implementation."""
        if code == "QSR10":
            return total * 0.9
        return total
