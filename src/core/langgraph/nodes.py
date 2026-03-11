from typing import Any, Dict
from langchain_core.messages import AIMessage, SystemMessage
from src.data.schemas.graph import GraphState
from src.services.llm import LLMService
from src.utils.graph import format_chat_history
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful AI assistant. You provide accurate, 
concise, and useful responses. Always be polite and professional."""


async def agent_node(state: GraphState, llm_service: LLMService) -> Dict[str, Any]:
    """Main agent node that calls the LLM with the current conversation state."""
    messages = state["messages"]
    trimmed = format_chat_history(list(messages), max_messages=20)
    full_messages = [SystemMessage(content=SYSTEM_PROMPT)] + trimmed

    try:
        response = await llm_service.ainvoke(full_messages)
        logger.info(f"Agent responded with {len(response.content)} chars")
        return {"messages": [response]}
    except Exception as e:
        logger.error(f"LLM invocation failed: {e}")
        error_msg = AIMessage(content="I'm sorry, I encountered an error. Please try again.")
        return {"messages": [error_msg]}


async def retrieval_node(state: GraphState) -> Dict[str, Any]:
    """Optional retrieval node for RAG-based augmentation."""
    # Placeholder for vector store retrieval logic
    # In a full implementation, this would query a vector database
    # and inject relevant context into the state
    return {"messages": state["messages"]}


async def guardrail_node(state: GraphState) -> Dict[str, Any]:
    """Guardrail node to validate and filter messages."""
    messages = state["messages"]
    if not messages:
        return {"messages": []}

    last_message = messages[-1]
    content = last_message.content if hasattr(last_message, 'content') else ""

    # Basic content check (extend with proper moderation in production)
    banned_patterns = ["<script>", "DROP TABLE", "rm -rf"]
    for pattern in banned_patterns:
        if pattern.lower() in content.lower():
            logger.warning(f"Guardrail blocked message containing: {pattern}")
            from langchain_core.messages import HumanMessage
            safe_messages = list(messages[:-1])
            return {"messages": safe_messages}

    return {"messages": messages}
