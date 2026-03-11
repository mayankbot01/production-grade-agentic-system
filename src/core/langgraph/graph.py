from functools import partial
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from src.data.schemas.graph import GraphState
from src.services.llm import LLMService
from .nodes import agent_node, retrieval_node, guardrail_node
from .edges import route_after_guardrail, route_after_retrieval, should_continue
import logging

logger = logging.getLogger(__name__)


def build_graph(llm_service: LLMService, use_memory: bool = True):
    """Build and compile the LangGraph state machine."""
    workflow = StateGraph(GraphState)

    # Bind llm_service to agent_node
    bound_agent = partial(agent_node, llm_service=llm_service)

    # Add nodes
    workflow.add_node("guardrail", guardrail_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("agent", bound_agent)

    # Set entry point
    workflow.set_entry_point("guardrail")

    # Add conditional edges
    workflow.add_conditional_edges(
        "guardrail",
        route_after_guardrail,
        {"agent": "retrieval", "end": END},
    )
    workflow.add_conditional_edges(
        "retrieval",
        route_after_retrieval,
        {"agent": "agent", "end": END},
    )
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"continue": "guardrail", "end": END},
    )

    # Compile with optional memory checkpointing
    if use_memory:
        memory = MemorySaver()
        app = workflow.compile(checkpointer=memory)
    else:
        app = workflow.compile()

    logger.info("LangGraph compiled successfully")
    return app
