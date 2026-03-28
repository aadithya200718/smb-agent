"""
LangGraph Workflow Definition.

Connects the seven agent nodes into a compiled StateGraph:
INPUT → THINK → PLAN → ACT → REVIEW → (UPDATE → ACT →)* RESPOND → END

Exports ``run_agent()`` as the single entry-point for processing a message.
"""

from typing import Any, Dict, Optional

from langgraph.graph import END, StateGraph
from langchain_core.messages import HumanMessage

from app.agent.state import AgentState
from app.agent.nodes import (
    input_node,
    think_node,
    plan_node,
    act_node,
    review_node,
    update_node,
    respond_node,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Build the graph ───────────────────────────────────────────────────

workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("input", input_node)
workflow.add_node("think", think_node)
workflow.add_node("plan", plan_node)
workflow.add_node("act", act_node)
workflow.add_node("review", review_node)    # NEW
workflow.add_node("update", update_node)    # NEW
workflow.add_node("respond", respond_node)

# Define edges
workflow.set_entry_point("input")
workflow.add_edge("input", "think")
workflow.add_edge("think", "plan")


def _should_act(state: AgentState) -> str:
    """
    Conditional edge after PLAN: skip ACT if there are no tools to run
    (e.g., for greetings or FAQs the LLM answers directly).
    """
    if state.get("tools_to_use"):
        return "act"
    return "respond"


workflow.add_conditional_edges("plan", _should_act, {"act": "act", "respond": "respond"})

# ACT always goes to REVIEW now
workflow.add_edge("act", "review")


def _should_retry(state: AgentState) -> str:
    """
    Conditional edge after REVIEW:
    - If validation passed → respond
    - If validation failed and retry budget > 0 → update (then retry)
    - If validation failed and budget exhausted → respond with error
    """
    validation = state.get("validation_result", {})
    retry_budget = state.get("retry_budget", 0)

    if validation and validation.get("passed", False):
        return "respond"
    elif retry_budget > 0:
        return "update"
    else:
        return "respond"


workflow.add_conditional_edges(
    "review",
    _should_retry,
    {
        "respond": "respond",
        "update": "update",
    }
)

# UPDATE → ACT (retry loop)
workflow.add_edge("update", "act")

# RESPOND → END
workflow.add_edge("respond", END)

# Compile once at module level
agent_graph = workflow.compile()


# ── Public API ────────────────────────────────────────────────────────

async def run_agent(
    message: str,
    user_phone: str,
    business_id: str,
    existing_messages: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Process a single user message through the full agent pipeline.

    Args:
        message: The user's WhatsApp text.
        user_phone: The sender's phone number.
        business_id: The identifier of the business being contacted.
        existing_messages: Optional prior messages for multi-turn context.

    Returns:
        The final AgentState dict containing the generated ``response``
        and a ``trace_log`` proving the autonomous decision chain.
    """
    logger.info("▶ run_agent called — phone=%s, biz=%s", user_phone, business_id)

    initial_messages = list(existing_messages or [])
    initial_messages.append(HumanMessage(content=message))

    initial_state: Dict[str, Any] = {
        "messages": initial_messages,
        "user_phone": user_phone,
        "business_id": business_id,
        "current_intent": None,
        "extracted_info": {},
        "user_memory": {},
        "tools_to_use": [],
        "tool_results": {},
        "response": None,
        "validation_result": None,
        "retry_count": 0,
        "retry_budget": 2,
        "trace_log": [],
        "failed_tools": [],
        "user_language": "en",
    }

    final_state = await agent_graph.ainvoke(initial_state)

    logger.info(
        "Agent finished — intent=%s, retries=%d, trace_steps=%d",
        final_state.get("current_intent"),
        final_state.get("retry_count", 0),
        len(final_state.get("trace_log", [])),
    )
    return final_state
