"""
Test Harness for QSR WhatsApp Bot.

Comprehensive tests for all new modules:
  - Petpooja POS integration
  - Razorpay Advanced integration
  - Autonomous Policy Engine
  - Deterministic Validators
  - Menu Ingestion Pipeline
  - WhatsApp Compliance
  - Monitoring tools
"""

import asyncio
import sys
from datetime import datetime, timezone, timedelta

# ── Test runner utility ───────────────────────────────────────────────

_tests_passed = 0
_tests_failed = 0


def _report(name: str, passed: bool, detail: str = ""):
    global _tests_passed, _tests_failed
    if passed:
        _tests_passed += 1
        print(f"  ✅ {name}")
    else:
        _tests_failed += 1
        print(f"  ❌ {name}: {detail}")


# ── Test: Petpooja POS ────────────────────────────────────────────────

async def test_petpooja():
    print("\n🧪 Petpooja POS Integration")
    from app.integrations.petpooja import petpooja_client

    # Test mock mode detection
    _report("Mock mode enabled", petpooja_client.mock_mode is True)

    # Test menu fetch
    menu = await petpooja_client.fetch_menu()
    _report("Fetch menu returns items", len(menu) > 0)
    _report("Menu items have required fields",
            all(m.get("name") and m.get("price") and m.get("item_id") for m in menu))

    # Test stock check
    stock = await petpooja_client.check_stock("PP001", 1)
    _report("Stock check returns availability", "available" in stock)
    _report("Stock check returns current_stock", "current_stock" in stock)

    # Test out of stock
    stock_oos = await petpooja_client.check_stock("PP005", 1)
    _report("Out of stock detected correctly", stock_oos["available"] is False)

    # Test price fetch
    price = await petpooja_client.get_item_price("PP001")
    _report("Price fetch returns float", isinstance(price, float) and price > 0)

    # Test POS order creation
    pos_order = await petpooja_client.create_pos_order(
        order_id="TEST-001",
        items=[{"item_id": "PP001", "quantity": 2, "unit_price": 149.0}],
        customer_phone="+919999999999",
    )
    _report("POS order created", pos_order.get("pos_order_id") is not None)
    _report("POS order has ETA", pos_order.get("estimated_time_minutes", 0) > 0)

    # Test stock deduction
    before = (await petpooja_client.check_stock("PP001"))["current_stock"]
    success = await petpooja_client.deduct_stock("PP001", 2)
    after = (await petpooja_client.check_stock("PP001"))["current_stock"]
    _report("Stock deduction succeeds", success is True)
    _report("Stock count decreased", after == before - 2)

    # Test alternatives suggestion
    alts = await petpooja_client.suggest_alternatives("PP005")
    _report("Alternatives suggested for OOS item", len(alts) > 0)


# ── Test: Razorpay Advanced ───────────────────────────────────────────

async def test_razorpay():
    print("\n🧪 Razorpay Advanced Integration")
    from app.integrations.razorpay_advanced import razorpay_service

    _report("Mock mode enabled", razorpay_service.mock_mode is True)

    # Test payment link creation
    result = await razorpay_service.create_payment_link(
        order_id="TEST-RZP-001",
        amount=299.0,
        customer_phone="+919999999999",
    )
    _report("Payment link created", result.get("short_url") is not None)
    _report("Payment link ID returned", result.get("payment_link_id") is not None)

    # Test webhook event handling
    event = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_123",
                    "notes": {"order_id": "TEST-RZP-001"},
                }
            }
        },
    }
    webhook_result = await razorpay_service.handle_webhook_event(event)
    _report("Webhook payment.captured handled", webhook_result.get("status") is not None)

    # Test refund
    refund = await razorpay_service.initiate_refund("pay_test_123", 100.0)
    _report("Refund initiated", refund.get("refund_id") is not None)
    _report("Refund status returned", refund.get("status") is not None)


# ── Test: Autonomous Policies ─────────────────────────────────────────

async def test_policies():
    print("\n🧪 Autonomous Policy Engine")
    from app.services.autonomous_policies import AutonomousPolicies

    # Test payment timeout — non-existent order
    result = await AutonomousPolicies.check_payment_timeout("NONEXISTENT-001")
    _report("Non-existent order returns none", result["action"] == "none")

    # Test escalation — low confidence
    esc = await AutonomousPolicies.check_escalation(confidence=0.5, retry_count=0)
    _report("Low confidence triggers escalation", esc["action"] == "escalate")

    # Test escalation — too many retries
    esc2 = await AutonomousPolicies.check_escalation(confidence=0.9, retry_count=3)
    _report("Retry limit triggers escalation", esc2["action"] == "escalate")

    # Test escalation — happy path
    esc3 = await AutonomousPolicies.check_escalation(confidence=0.9, retry_count=0)
    _report("Good confidence no escalation", esc3["action"] == "none")

    # Test inventory policies — out of stock
    inv = await AutonomousPolicies.check_inventory_policies("PP005", stock_count=0)
    _report("OOS triggers out_of_stock action", inv.get("action") == "out_of_stock")

    # Test inventory policies — low stock
    inv2 = await AutonomousPolicies.check_inventory_policies("PP001", stock_count=3)
    _report("Low stock triggers warning", inv2.get("action") == "low_stock_warning")

    # Test fraud — high value
    fraud = await AutonomousPolicies.check_fraud_signals("+919999999999", order_value=6000)
    _report("High value triggers verification", fraud.get("action") == "require_verification")


# ── Test: Validators ──────────────────────────────────────────────────

async def test_validators():
    print("\n🧪 Deterministic Validators")
    from app.validators.order_validator import OrderValidator
    from app.validators.pricing_validator import PricingValidator
    from app.validators.availability_validator import AvailabilityValidator

    # Order validator
    _report("Valid quantities pass",
            OrderValidator.validate_quantities([{"quantity": 2}, {"quantity": 1}]))
    _report("Zero quantity fails",
            not OrderValidator.validate_quantities([{"quantity": 0}]))
    _report("Empty items fails",
            not OrderValidator.validate_quantities([]))

    # Phone validation
    _report("Valid Indian phone passes",
            OrderValidator.validate_phone("+919876543210"))
    _report("Invalid phone fails",
            not OrderValidator.validate_phone("+12345"))

    # Pricing validator
    items = [{"quantity": 2, "unit_price": 149.0}, {"quantity": 1, "unit_price": 89.0}]
    _report("Correct total validates",
            PricingValidator.validate_total_matches(items, 387.0))
    _report("Incorrect total fails",
            not PricingValidator.validate_total_matches(items, 400.0))

    # Discount
    _report("QSR10 discount applies",
            PricingValidator.apply_valid_discount(100.0, "QSR10") == 90.0)
    _report("Unknown code no discount",
            PricingValidator.apply_valid_discount(100.0, "FAKE") == 100.0)

    # Availability
    _report("Restaurant availability check runs",
            isinstance(AvailabilityValidator.is_restaurant_open(), bool))


# ── Test: WhatsApp Compliance ─────────────────────────────────────────

async def test_compliance():
    print("\n🧪 WhatsApp Compliance")
    from app.services.whatsapp_compliance import (
        session_manager, template_manager, whatsapp_compliance
    )

    # Template manager
    tmpl = template_manager.get_template(
        "order_confirmation",
        order_id="TEST-001", total="299", eta="20", tracking_link="https://track.me"
    )
    _report("Template renders correctly", tmpl is not None and "TEST-001" in tmpl["body"])
    _report("Template has correct name", tmpl["name"] == "qsr_order_confirmed")

    # Missing template
    bad_tmpl = template_manager.get_template("nonexistent")
    _report("Missing template returns None", bad_tmpl is None)

    # List templates
    all_tmpls = template_manager.list_templates()
    _report("Templates list is not empty", len(all_tmpls) > 0)


# ── Test: Monitoring ──────────────────────────────────────────────────

async def test_monitoring():
    print("\n🧪 Monitoring & SLA")
    from app.monitoring.performance_tracker import track_performance, SLA_TARGETS_MS
    from app.monitoring.quality_metrics import quality_metrics

    # SLA targets defined
    _report("SLA targets configured", len(SLA_TARGETS_MS) > 0)
    _report("faq_response SLA exists", "faq_response" in SLA_TARGETS_MS)

    # Quality metrics — tool success rate
    results = {"menu": [...], "order_id": "ORD-001", "total": 299.0}
    rate = quality_metrics.calculate_tool_success_rate(results)
    _report("100% success rate for clean results", rate == 100.0)

    results_with_error = {"menu": [...], "get_menu_error": "timeout"}
    rate2 = quality_metrics.calculate_tool_success_rate(results_with_error)
    _report("Error decreases success rate", rate2 < 100.0)

    # Validation pass rate
    runs = [True, True, False, True]
    pass_rate = quality_metrics.calculate_validation_pass_rate(runs)
    _report("Validation pass rate calculated", pass_rate == 75.0)

    # Circuit breaker
    from app.utils.circuit_breaker import CircuitBreaker
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
    _report("Circuit breaker starts CLOSED", cb.state == "CLOSED")


# ── Test: Menu Pipeline ───────────────────────────────────────────────

async def test_menu_pipeline():
    print("\n🧪 Menu Ingestion Pipeline")
    from app.services.menu_ingestion import MenuIngestionPipeline

    # Test hash computation
    items = [{"name": "Test", "price": 100}]
    hash1 = MenuIngestionPipeline._compute_menu_hash(items)
    hash2 = MenuIngestionPipeline._compute_menu_hash(items)
    _report("Same items produce same hash", hash1 == hash2)

    items2 = [{"name": "Test", "price": 200}]
    hash3 = MenuIngestionPipeline._compute_menu_hash(items2)
    _report("Different items produce different hash", hash1 != hash3)


# ── Main ──────────────────────────────────────────────────────────────

async def run_all_tests():
    """Run all test suites."""
    print("=" * 60)
    print("  QSR WhatsApp Bot — Test Harness")
    print("=" * 60)

    # Tests that don't need MongoDB
    await test_validators()
    await test_monitoring()

    # Tests that need Petpooja mock (no DB)
    await test_petpooja()

    # Tests that may need MongoDB
    try:
        from app.core.database import MongoDB
        await MongoDB.connect()
        print("\n  📦 MongoDB connected — running DB-dependent tests")

        await test_razorpay()
        await test_policies()
        await test_compliance()
        await test_menu_pipeline()

        await MongoDB.disconnect()
    except Exception as e:
        print(f"\n  ⚠️  MongoDB unavailable ({e}) — skipping DB tests")

    print("\n" + "=" * 60)
    print(f"  Results: {_tests_passed} passed, {_tests_failed} failed")
    print("=" * 60)

    return _tests_failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
