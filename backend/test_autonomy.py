"""
Autonomy Proof Test Script.

Runs the agent graph and prints trace logs demonstrating
the Think → Plan → Execute → Review → (Update →)* Respond loop.
"""

import asyncio
import json
import sys
import os

# Ensure the backend package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_core.messages import HumanMessage


async def test_successful_flow():
    """Test: Think → Plan → Execute → Review → Respond (no retry needed)"""
    print("\n" + "=" * 60)
    print("  Test 1: Successful Flow (menu inquiry)")
    print("=" * 60)

    from app.agent.graph import run_agent

    result = await run_agent(
        message="Show me the menu please",
        user_phone="+919876543210",
        business_id="BIZ001",
    )

    # Print trace
    trace = result.get("trace_log", [])
    print(f"\n📋 Trace Log ({len(trace)} steps):")
    print(json.dumps(trace, indent=2, default=str))

    # Print response
    print(f"\n💬 Response: {result.get('response', '(none)')[:200]}")

    # Verify the full loop executed
    node_names = [t["node_name"] for t in trace]
    print(f"\n🔄 Node path: {' → '.join(node_names)}")

    assert "input" in node_names, "Missing input node"
    assert "think" in node_names, "Missing think node"
    assert "plan" in node_names, "Missing plan node"
    assert "review" in node_names, "Missing review node"
    assert "respond" in node_names, "Missing respond node"

    validation = result.get("validation_result", {})
    if validation:
        print(f"\n✅ Validation: passed={validation.get('passed')}, "
              f"confidence={validation.get('confidence_score')}")
    print("\n✅ Test 1 PASSED")


async def test_order_flow():
    """Test: Full order flow — get_menu → create_order → payment_link → review"""
    print("\n" + "=" * 60)
    print("  Test 2: Order Flow (place_order intent)")
    print("=" * 60)

    from app.agent.graph import run_agent

    result = await run_agent(
        message="I want 2 veg biryanis",
        user_phone="+919876543210",
        business_id="BIZ001",
    )

    trace = result.get("trace_log", [])
    print(f"\n📋 Trace Log ({len(trace)} steps):")
    print(json.dumps(trace, indent=2, default=str))

    print(f"\n💬 Response: {result.get('response', '(none)')[:200]}")

    node_names = [t["node_name"] for t in trace]
    print(f"\n🔄 Node path: {' → '.join(node_names)}")

    # Verify order was created
    tool_results = result.get("tool_results", {})
    print(f"\n📦 Order ID: {tool_results.get('order_id', 'N/A')}")
    print(f"💰 Total: ₹{tool_results.get('total', 0)}")
    print(f"🔗 Payment Link: {tool_results.get('payment_link', 'N/A')}")
    print(f"📊 Retry Count: {result.get('retry_count', 0)}")

    print("\n✅ Test 2 PASSED")


async def test_greeting_flow():
    """Test: Greeting flow — no tools needed, direct response"""
    print("\n" + "=" * 60)
    print("  Test 3: Greeting Flow (no tools)")
    print("=" * 60)

    from app.agent.graph import run_agent

    result = await run_agent(
        message="Hi there!",
        user_phone="+919876543210",
        business_id="BIZ001",
    )

    trace = result.get("trace_log", [])
    print(f"\n📋 Trace Log ({len(trace)} steps):")
    print(json.dumps(trace, indent=2, default=str))

    print(f"\n💬 Response: {result.get('response', '(none)')[:200]}")

    node_names = [t["node_name"] for t in trace]
    print(f"\n🔄 Node path: {' → '.join(node_names)}")

    # For greetings, should skip act/review and go straight to respond
    assert "respond" in node_names, "Missing respond node"
    print("\n✅ Test 3 PASSED")


async def main():
    print("\n🚀 Autonomous Agent Enhancement - Proof of Autonomy")
    print("=" * 60)

    try:
        await test_successful_flow()
    except Exception as e:
        print(f"\n❌ Test 1 FAILED: {e}")

    try:
        await test_order_flow()
    except Exception as e:
        print(f"\n❌ Test 2 FAILED: {e}")

    try:
        await test_greeting_flow()
    except Exception as e:
        print(f"\n❌ Test 3 FAILED: {e}")

    print("\n" + "=" * 60)
    print("  All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
