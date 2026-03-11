from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from typing import List, Dict, Any
import json


def dump_messages(messages: List[BaseMessage]) -> List[Dict[str, Any]]:
    """Serialize LangChain messages to JSON-serializable format."""
    serialized = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            serialized.append({"role": "human", "content": msg.content})
        elif isinstance(msg, AIMessage):
            serialized.append({"role": "ai", "content": msg.content})
        else:
            serialized.append({"role": "unknown", "content": str(msg.content)})
    return serialized


def load_messages(data: List[Dict[str, Any]]) -> List[BaseMessage]:
    """Deserialize messages from JSON format to LangChain messages."""
    messages = []
    for item in data:
        role = item.get("role", "unknown")
        content = item.get("content", "")
        if role == "human":
            messages.append(HumanMessage(content=content))
        elif role == "ai":
            messages.append(AIMessage(content=content))
    return messages


def prepare_messages(history: List[BaseMessage], new_message: str) -> List[BaseMessage]:
    """Prepare message list by appending a new human message."""
    messages = list(history)
    messages.append(HumanMessage(content=new_message))
    return messages


def process_llm_response(response: AIMessage) -> str:
    """Extract clean text content from an LLM response."""
    if isinstance(response, AIMessage):
        return response.content.strip()
    return str(response).strip()


def format_chat_history(messages: List[BaseMessage], max_messages: int = 20) -> List[BaseMessage]:
    """Trim chat history to the last N messages to avoid context overflow."""
    if len(messages) > max_messages:
        return messages[-max_messages:]
    return messages
