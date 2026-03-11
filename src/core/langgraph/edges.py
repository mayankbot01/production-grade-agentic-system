from typing import Literal
from src.data.schemas.graph import GraphState
from langchain_core.messages import AIMessage
import logging

logger = logging.getLogger(__name__)


def should_continue(state: GraphState) -> Literal["continue", "end"]:
    """Determine if the graph should continue or end based on current state."""
    messages = state.get("messages", [])
    if not messages:
        return "end"

    last_message = messages[-1]
    # If the last message is from the AI, we're done for this turn
    if isinstance(last_message, AIMessage):
        return "end"

    return "continue"


def route_after_guardrail(state: GraphState) -> Literal["agent", "end"]:
    """Route to agent or end after guardrail check."""
    messages = state.get("messages", [])
    if not messages:
        logger.warning("No messages after guardrail - routing to end")
        return "end"
    return "agent"


def route_after_retrieval(state: GraphState) -> Literal["agent", "end"]:
    """Route after retrieval node."""
    messages = state.get("messages", [])
    if not messages:
        return "end"
    return "agent"
