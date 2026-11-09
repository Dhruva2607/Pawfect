"""
Conversational Chatbot endpoints with Server-Sent Events (SSE) token streaming.
[FROM MARKDOWN] matches Step 3.1: POST /api/v1/chat/message and Section 4.
"""

import json
import asyncio
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Header
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.database.connection import get_async_db
from app.services.graph import run_matchmaker_turn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatMessageRequest(BaseModel):
    session_id: str = Field(..., description="Unique conversation session ID")
    message: str = Field(..., description="User message content")
    user_id: Optional[str] = Field(None, description="Optional associated user ID")
    stream: Optional[bool] = Field(False, description="Set true for real-time Server-Sent Events token stream")


class ChatMessageResponse(BaseModel):
    session_id: str
    response_message: str
    quick_replies: List[str] = Field(default_factory=list)
    is_complete: bool = False
    candidate_matches: List[Dict[str, Any]] = Field(default_factory=list)
    evaluations: List[Dict[str, Any]] = Field(default_factory=list)
    extracted_constraints: Dict[str, Any] = Field(default_factory=dict)


async def _load_session_data(session_id: str) -> tuple[list, dict]:
    """Retrieves conversation history and prior constraints from MongoDB user_sessions."""
    db = get_async_db()
    session_doc = await db["user_sessions"].find_one({"_id": session_id})
    if session_doc:
        history = session_doc.get("conversation_history", [])
        constraints = session_doc.get("extracted_constraints", {})
        return history, constraints
    return [], {}


async def _save_session_data(
    session_id: str,
    user_id: Optional[str],
    user_message: str,
    bot_message: str,
    constraints: dict,
    checkpoint: dict
):
    """Persists conversation history and state checkpoint in MongoDB user_sessions."""
    db = get_async_db()
    now = datetime.now(timezone.utc)

    user_entry = {"role": "user", "content": user_message, "timestamp": now.isoformat()}
    bot_entry = {"role": "assistant", "content": bot_message, "timestamp": now.isoformat()}

    await db["user_sessions"].update_one(
        {"_id": session_id},
        {
            "$setOnInsert": {"user_id": user_id, "created_at": now},
            "$push": {"conversation_history": {"$each": [user_entry, bot_entry]}},
            "$set": {
                "extracted_constraints": constraints,
                "state_checkpoint": checkpoint,
                "updated_at": now
            }
        },
        upsert=True
    )


async def _generate_sse_stream(
    session_id: str,
    user_id: Optional[str],
    user_message: str,
    history: list,
    prior_constraints: dict
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Asynchronous event generator streaming tokens and typing indicators via SSE.
    [FROM MARKDOWN: Step 3.1 & Section 4]
    """
    # 1. Emit typing indicator
    yield {
        "event": "typing",
        "data": json.dumps({"status": "thinking", "session_id": session_id})
    }
    await asyncio.sleep(0.05)

    # 2. Execute state machine turn in worker thread
    loop = asyncio.get_running_loop()
    result_state = await loop.run_in_executor(
        None,
        run_matchmaker_turn,
        session_id,
        user_message,
        history,
        prior_constraints
    )

    response_text = result_state.get("response_message", "")
    quick_replies = result_state.get("quick_replies", [])
    is_complete = result_state.get("is_complete", False)
    candidates = result_state.get("candidate_matches", [])
    evaluations = result_state.get("evaluations", [])
    updated_constraints = result_state.get("extracted_constraints", prior_constraints)

    # 3. Stream response tokens word by word with low latency [FROM MARKDOWN: Section 4]
    words = response_text.split(" ")
    for idx, word in enumerate(words):
        chunk = word + (" " if idx < len(words) - 1 else "")
        yield {
            "event": "token",
            "data": json.dumps({"token": chunk, "session_id": session_id})
        }
        await asyncio.sleep(0.02)  # Natural typing rhythm

    # 4. If quick replies exist, emit quick-reply chips
    if quick_replies:
        yield {
            "event": "quick_replies",
            "data": json.dumps({"quick_replies": quick_replies, "session_id": session_id})
        }

    # 5. If matches are found, emit matches and evaluations
    if is_complete and (candidates or evaluations):
        yield {
            "event": "matches",
            "data": json.dumps({
                "candidate_matches": candidates,
                "evaluations": evaluations,
                "session_id": session_id
            })
        }

    # 6. Emit done event
    yield {
        "event": "done",
        "data": json.dumps({
            "session_id": session_id,
            "is_complete": is_complete,
            "response_message": response_text
        })
    }

    # 7. Persist session state to MongoDB
    await _save_session_data(
        session_id=session_id,
        user_id=user_id,
        user_message=user_message,
        bot_message=response_text,
        constraints=updated_constraints,
        checkpoint={"is_complete": is_complete}
    )


@router.post("/message", summary="Send chat message (supports JSON or SSE token streaming)")
async def send_chat_message(
    request_data: ChatMessageRequest,
    req: Request,
    accept: Optional[str] = Header(None)
):
    """
    [FROM MARKDOWN: Step 3.1 & Section 4]
    POST /api/v1/chat/message
    Handles incoming user messages through the LangGraph AI Counselor.
    Supports real-time SSE token streaming when stream=True or Accept: text/event-stream.
    """
    history, prior_constraints = await _load_session_data(request_data.session_id)

    wants_stream = request_data.stream or (accept and "text/event-stream" in accept)

    if wants_stream:
        return EventSourceResponse(
            _generate_sse_stream(
                session_id=request_data.session_id,
                user_id=request_data.user_id,
                user_message=request_data.message,
                history=history,
                prior_constraints=prior_constraints
            )
        )

    # Standard JSON flow
    loop = asyncio.get_running_loop()
    result_state = await loop.run_in_executor(
        None,
        run_matchmaker_turn,
        request_data.session_id,
        request_data.message,
        history,
        prior_constraints
    )

    response_text = result_state.get("response_message", "")
    updated_constraints = result_state.get("extracted_constraints", prior_constraints)

    await _save_session_data(
        session_id=request_data.session_id,
        user_id=request_data.user_id,
        user_message=request_data.message,
        bot_message=response_text,
        constraints=updated_constraints,
        checkpoint={"is_complete": result_state.get("is_complete", False)}
    )

    return ChatMessageResponse(
        session_id=request_data.session_id,
        response_message=response_text,
        quick_replies=result_state.get("quick_replies", []),
        is_complete=result_state.get("is_complete", False),
        candidate_matches=result_state.get("candidate_matches", []),
        evaluations=result_state.get("evaluations", []),
        extracted_constraints=updated_constraints
    )

