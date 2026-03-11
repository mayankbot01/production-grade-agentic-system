from fastapi import APIRouter, HTTPException, Depends, status
from src.data.schemas.chat import ChatRequest, ChatResponse, Message
from src.data.schemas.graph import GraphState
from src.services.database import DatabaseService, get_db
from src.services.llm import LLMService
from src.core.langgraph.graph import build_graph
from src.utils.auth import verify_token
from src.utils.graph import dump_messages, load_messages
from src.utils.sanitization import sanitize_string
from langchain_core.messages import HumanMessage
import uuid
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

_llm_service = LLMService()
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph(_llm_service, use_memory=True)
    return _graph


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: str = Depends(verify_token),
    db: DatabaseService = Depends(get_db),
):
    """Send a message and get an AI response."""
    session_id = request.session_id or str(uuid.uuid4())
    user_message = sanitize_string(request.message)

    if not user_message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty")

    # Load existing session messages
    raw_messages = await db.get_session_messages(session_id)
    history = load_messages(raw_messages)

    # Ensure session exists
    try:
        user = await db.get_user_by_username(current_user)
        if user:
            await db.create_session(user_id=user["id"], session_id=session_id)
    except Exception:
        pass  # Session may already exist

    # Save user message
    await db.save_message(session_id=session_id, role="human", content=user_message)

    # Run graph
    graph = get_graph()
    history.append(HumanMessage(content=user_message))
    initial_state = GraphState(messages=history)

    config = {"configurable": {"thread_id": session_id}}
    result = await graph.ainvoke(initial_state, config=config)

    # Extract response
    result_messages = result.get("messages", [])
    if not result_messages:
        raise HTTPException(status_code=500, detail="No response from agent")

    ai_response = result_messages[-1].content
    await db.save_message(session_id=session_id, role="ai", content=ai_response)

    logger.info(f"Chat completed for session {session_id}")
    return ChatResponse(
        session_id=session_id,
        message=ai_response,
        role="ai"
    )


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    current_user: str = Depends(verify_token),
    db: DatabaseService = Depends(get_db),
):
    """Get chat history for a session."""
    messages = await db.get_session_messages(session_id)
    return {"session_id": session_id, "messages": messages}
