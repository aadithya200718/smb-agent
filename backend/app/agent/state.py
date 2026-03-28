"""
Agent State definition.

Defines the structure of the data passed between nodes in the LangGraph workflow.
Provides both short-term memory (conversation context) and extracted details.
"""

from typing import Annotated, Any, Dict, List, Optional, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ObjectDetails(TypedDict, total=False):
    """Container for extracted parameters like item and quantity."""
    item: Optional[str]
    quantity: Optional[int]



class ToolResultData(TypedDict, total=False):
    """Container for the output of executed tools."""
    menu: List[Dict[str, Any]]
    order_id: Optional[str]
    total: Optional[float]
    payment_link: Optional[str]


class ValidationResult(TypedDict):
    passed: bool
    confidence_score: float
    failures: List[str]
    failed_tool_names: List[str]


class TraceLog(TypedDict):
    node_name: str
    timestamp: str
    input_summary: dict
    output_summary: dict
    decision: Optional[str]


class AgentState(TypedDict):
    """
    Main state object for the AI WhatsApp Assistant workflow.

    Fields:
        messages: List of conversing messages (auto-appended by LangGraph)
        user_phone: The customer's WhatsApp number
        business_id: The identifier for the business they are messaging
        current_intent: The inferred goal (e.g., 'place_order', 'check_status')
        extracted_info: Details extracted from the message
        tools_to_use: Names of the tools the agent decided to execute
        tool_results: Data returned from the executed tools
        response: The final generated reply to the user
    """

    # 'add_messages' ensures new messages are appended rather than overwriting
    messages: Annotated[List[BaseMessage], add_messages]

    user_phone: str
    business_id: str

    current_intent: Optional[str]
    extracted_info: ObjectDetails

    tools_to_use: List[str]
    tool_results: ToolResultData
    response: Optional[str]

    # User context
    user_memory: Dict[str, Any]
    user_language: str

    # Validation / retry fields
    validation_result: Optional[ValidationResult]
    retry_count: int
    retry_budget: int
    trace_log: List[TraceLog]
    failed_tools: List[str]
