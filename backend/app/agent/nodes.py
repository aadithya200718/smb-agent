"""
Agent Graph Nodes (QSR-Focused).

Each node is a pure function: (state: AgentState) → dict of updated fields.
LangGraph merges the returned dict back into the state automatically.

Flow: INPUT → THINK → PLAN → ACT → REVIEW → (UPDATE → ACT →)* RESPOND
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict

from langchain_core.messages import AIMessage, HumanMessage

from app.agent.state import AgentState
from app.agent import tools as agent_tools
from app.models.order import OrderItem
from app.services.llm import GroqService
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _conversation_history_str(state: AgentState) -> str:
    """Build a flat text summary of the last 10 messages."""
    lines: list[str] = []
    for msg in state.get("messages", [])[-10:]:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines)


def _now_iso() -> str:
    """Return current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat()


# ── 1. INPUT NODE ──────────────────────────────────────────────────────

async def input_node(state: AgentState) -> Dict[str, Any]:
    """
    Receive the incoming message and initialise blank state fields.
    """
    latest = state["messages"][-1].content if state["messages"] else ""
    logger.info("INPUT NODE - message: %s", latest[:80])

    trace_entry = {
        "node_name": "input",
        "timestamp": _now_iso(),
        "input_summary": {"message": latest[:100]},
        "output_summary": {"action": "initialized state"},
        "decision": "Message received",
    }

    return {
        "current_intent": None,
        "extracted_info": {},
        "tools_to_use": [],
        "tool_results": {},
        "response": None,
        "validation_result": None,
        "retry_count": 0,
        "retry_budget": 2,
        "failed_tools": [],
        "trace_log": state.get("trace_log", []) + [trace_entry],
    }


# ── 2. THINK NODE ─────────────────────────────────────────────────────

async def think_node(state: AgentState) -> Dict[str, Any]:
    """
    Classify the user's intent and extract entities using the LLM.
    QSR-focused: English only, no language detection or memory retrieval.
    """
    latest_msg = state["messages"][-1].content if state["messages"] else ""
    history = _conversation_history_str(state)

    trace_entry = {
        "node_name": "think",
        "timestamp": _now_iso(),
        "input_summary": {"message": latest_msg[:100]},
        "output_summary": {},
        "decision": None,
    }

    # Classify intent
    intent = await GroqService.classify_intent(latest_msg, history)

    # Extract entities
    entities = await GroqService.extract_entities(latest_msg, intent, history)

    logger.info("THINK NODE - intent=%s, entities=%s", intent, entities)

    trace_entry["output_summary"] = {
        "intent": intent,
        "entities": entities,
    }
    trace_entry["decision"] = f"Intent: {intent}"

    return {
        "current_intent": intent,
        "extracted_info": entities,
        "trace_log": state.get("trace_log", []) + [trace_entry],
    }


# ── 3. PLAN NODE ──────────────────────────────────────────────────────

async def plan_node(state: AgentState) -> Dict[str, Any]:
    """
    Decide which tools to execute based on the classified intent.
    QSR-focused: only get_menu, create_order, generate_payment_link.
    """
    intent = state.get("current_intent", "unknown")

    tool_map: Dict[str, list[str]] = {
        "menu_inquiry": ["get_menu"],
        "place_order": ["get_menu", "create_order", "generate_payment_link"],
        "faq": [],
        "unknown": [],
    }

    planned = tool_map.get(intent, [])
    logger.info("PLAN NODE - tools=%s", planned)

    trace_entry = {
        "node_name": "plan",
        "timestamp": _now_iso(),
        "input_summary": {"intent": intent},
        "output_summary": {"tools": planned},
        "decision": f"Tools: {planned}",
    }

    return {
        "tools_to_use": planned,
        "trace_log": state.get("trace_log", []) + [trace_entry],
    }


# ── 4. ACT NODE ───────────────────────────────────────────────────────

async def act_node(state: AgentState) -> Dict[str, Any]:
    """
    Execute each planned tool sequentially and aggregate results.
    """
    tools = state.get("tools_to_use", [])
    results: Dict[str, Any] = dict(state.get("tool_results", {}))  # preserve prior successes
    biz = state.get("business_id", "BIZ001")
    phone = state.get("user_phone", "")
    info = state.get("extracted_info", {})

    trace_entry = {
        "node_name": "act",
        "timestamp": _now_iso(),
        "input_summary": {"tools_to_execute": tools},
        "output_summary": {},
        "decision": None,
    }

    executed = 0
    errors: list[str] = []

    for tool_name in tools:
        try:
            if tool_name == "get_menu":
                menu_items = await agent_tools.get_menu(biz)
                results["menu"] = [m.model_dump() for m in menu_items]

            elif tool_name == "create_order":
                item_name = info.get("item", "")
                qty = info.get("quantity", 1) or 1

                unit_price = 0.0
                item_id = ""
                for m in results.get("menu", []):
                    if item_name and item_name.lower() in m["name"].lower():
                        unit_price = m["price"]
                        item_id = m["item_id"]
                        item_name = m["name"]
                        break

                if not item_id and results.get("menu"):
                    m = results["menu"][0]
                    unit_price = m["price"]
                    item_id = m["item_id"]
                    item_name = m["name"]

                order_items = [
                    OrderItem(
                        item_id=item_id or "UNKNOWN",
                        name=item_name or "Unknown Item",
                        quantity=qty,
                        unit_price=unit_price,
                    )
                ]
                order = await agent_tools.create_order({
                    "business_id": biz,
                    "customer_phone": phone,
                    "items": order_items,
                })
                results["order_id"] = order.order_id
                results["total"] = order.total

            elif tool_name == "generate_payment_link":
                oid = results.get("order_id", "ORD-000")
                total = results.get("total", 0.0)
                link = await agent_tools.generate_payment_link(oid, total, phone)
                results["payment_link"] = link

            executed += 1

        except Exception as exc:
            logger.error("Tool '%s' failed: %s", tool_name, exc)
            results[f"{tool_name}_error"] = str(exc)
            errors.append(f"{tool_name}: {exc}")

    trace_entry["output_summary"] = {
        "executed": executed,
        "result_keys": list(results.keys()),
        "errors": errors,
    }
    trace_entry["decision"] = f"Executed {executed} tools" + (
        f" ({len(errors)} errors)" if errors else ""
    )

    logger.info("ACT NODE - executed %d tools, results keys=%s", executed, list(results.keys()))
    return {
        "tool_results": results,
        "trace_log": state.get("trace_log", []) + [trace_entry],
    }


# ── 5. REVIEW NODE ───────────────────────────────────────────────────

async def review_node(state: AgentState) -> Dict[str, Any]:
    """
    Validates tool outputs against quality criteria.
    Returns validation result with confidence score.
    """
    trace_entry = {
        "node_name": "review",
        "timestamp": _now_iso(),
        "input_summary": {"tools_executed": list(state.get("tool_results", {}).keys())},
        "output_summary": {},
        "decision": None,
    }

    failures: list[str] = []
    failed_tools: list[str] = []
    confidence_score = 1.0

    tool_results = state.get("tool_results", {})

    # Check for explicit tool errors
    for key in tool_results:
        if key.endswith("_error"):
            tool_name = key.replace("_error", "")
            failures.append(f"Tool {tool_name} errored: {tool_results[key]}")
            failed_tools.append(tool_name)
            confidence_score = 0.0

    # Validate get_menu results
    if "menu" in tool_results:
        menu = tool_results["menu"]
        if not menu or len(menu) == 0:
            failures.append("Menu is empty")
            failed_tools.append("get_menu")
            confidence_score = 0.0
        else:
            for item in menu:
                if not item.get("name") or item.get("price", 0) <= 0:
                    failures.append(f"Invalid menu item: {item}")
                    failed_tools.append("get_menu")
                    confidence_score = min(confidence_score, 0.5)

    # Validate create_order results
    if "order_id" in tool_results:
        order_id = tool_results["order_id"]
        total = tool_results.get("total", 0)

        if not order_id or order_id == "":
            failures.append("Order ID is missing")
            failed_tools.append("create_order")
            confidence_score = 0.0

        if total <= 0:
            failures.append("Order total is invalid (<=0)")
            failed_tools.append("create_order")
            confidence_score = 0.0

    # Validate payment_link results
    if "payment_link" in tool_results:
        link = tool_results["payment_link"]
        if not link or not (link.startswith("http://") or link.startswith("https://")):
            failures.append("Payment link is invalid")
            failed_tools.append("generate_payment_link")
            confidence_score = 0.0

    passed = len(failures) == 0
    unique_failed = list(set(failed_tools))

    validation_result = {
        "passed": passed,
        "confidence_score": confidence_score,
        "failures": failures,
        "failed_tool_names": unique_failed,
    }

    trace_entry["output_summary"] = validation_result
    trace_entry["decision"] = "PASS" if passed else "FAIL"

    logger.info("REVIEW NODE - passed=%s, confidence=%.2f, failures=%s",
                passed, confidence_score, failures)

    return {
        "validation_result": validation_result,
        "failed_tools": unique_failed,
        "trace_log": state.get("trace_log", []) + [trace_entry],
    }


# ── 6. UPDATE NODE ───────────────────────────────────────────────────

async def update_node(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes validation failures and generates revised tool plan.
    Implements retry logic with budget control.
    """
    trace_entry = {
        "node_name": "update",
        "timestamp": _now_iso(),
        "input_summary": {
            "validation_result": state.get("validation_result"),
            "retry_count": state.get("retry_count", 0),
        },
        "output_summary": {},
        "decision": None,
    }

    new_retry_count = state.get("retry_count", 0) + 1
    new_retry_budget = state.get("retry_budget", 2) - 1

    failed_tools = state.get("failed_tools", [])

    revised_tools: list[str] = []

    if "get_menu" in failed_tools:
        revised_tools.append("get_menu")

    if "create_order" in failed_tools:
        if "get_menu" not in revised_tools and "menu" not in state.get("tool_results", {}):
            revised_tools.append("get_menu")
        revised_tools.append("create_order")

    if "generate_payment_link" in failed_tools:
        if state.get("tool_results", {}).get("order_id"):
            revised_tools.append("generate_payment_link")

    revised_tools = revised_tools[:5]

    trace_entry["output_summary"] = {
        "revised_tools": revised_tools,
        "retry_count": new_retry_count,
        "retry_budget": new_retry_budget,
    }
    trace_entry["decision"] = f"RETRY with {len(revised_tools)} tools"

    logger.info("UPDATE NODE - retry #%d, revised_tools=%s", new_retry_count, revised_tools)

    return {
        "tools_to_use": revised_tools,
        "retry_count": new_retry_count,
        "retry_budget": new_retry_budget,
        "trace_log": state.get("trace_log", []) + [trace_entry],
    }


# ── 7. RESPOND NODE ──────────────────────────────────────────────────

async def respond_node(state: AgentState) -> Dict[str, Any]:
    """
    Use the LLM to craft the final customer-facing WhatsApp message.
    Handles both success and error scenarios based on validation results.
    English-only QSR responses.
    """
    latest_msg = state["messages"][-1].content if state["messages"] else ""
    history = _conversation_history_str(state)

    trace_entry = {
        "node_name": "respond",
        "timestamp": _now_iso(),
        "input_summary": {
            "validation_passed": state.get("validation_result", {}).get("passed", True)
            if state.get("validation_result") else True,
            "retry_count": state.get("retry_count", 0),
        },
        "output_summary": {},
        "decision": None,
    }

    validation = state.get("validation_result") or {}

    # Check if validation failed and we exhausted retries
    if validation and not validation.get("passed", True):
        failures = validation.get("failures", [])
        retry_count = state.get("retry_count", 0)

        logger.warning("RESPOND NODE - generating error response (failures=%s, retries=%d)",
                        failures, retry_count)

        from app.agent.prompts import ERROR_RESPONSE_PROMPT

        error_prompt = ERROR_RESPONSE_PROMPT.format(
            failures=", ".join(failures),
            retry_count=retry_count,
        )

        response_text = await GroqService.generate_response(
            user_message=latest_msg,
            intent=state.get("current_intent", "unknown"),
            tool_results={"system_note": error_prompt},
            user_memory={},
            conversation_history=history,
        )
        trace_entry["decision"] = "ERROR_RESPONSE"
    else:
        # Normal response generation
        response_text = await GroqService.generate_response(
            user_message=latest_msg,
            intent=state.get("current_intent", "unknown"),
            tool_results=state.get("tool_results", {}),
            user_memory={},
            conversation_history=history,
        )

        if state.get("retry_count", 0) > 0:
            trace_entry["decision"] = "SUCCESS_AFTER_RETRY"
        else:
            trace_entry["decision"] = "SUCCESS_RESPONSE"

    trace_entry["output_summary"] = {
        "response_length": len(response_text),
    }

    logger.info("RESPOND NODE - response length=%d, decision=%s",
                len(response_text), trace_entry["decision"])

    return {
        "response": response_text,
        "messages": [AIMessage(content=response_text)],
        "trace_log": state.get("trace_log", []) + [trace_entry],
    }
