"""
Conversational Chatbot endpoints with Server-Sent Events (SSE) token streaming.
[FROM MARKDOWN] matches Step 3.1: POST /api/v1/chat/message and Section 4.
"""

import json
import asyncio
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime, timezone
from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.database.connection import get_async_db
from app.services.graph import run_matchmaker_turn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatMessageRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128, description="Unique conversation session ID")
    message: str = Field(..., min_length=1, max_length=4000, description="User message content")
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


async def _load_session_data(session_id: str) -> tuple[list, dict, Optional[str]]:
    """Retrieves conversation history, prior constraints, and owner from MongoDB user_sessions."""
    db = get_async_db()
    session_doc = await db["user_sessions"].find_one({"_id": session_id})
    if session_doc:
        history = session_doc.get("conversation_history", [])
        constraints = session_doc.get("extracted_constraints", {})
        return history, constraints, session_doc.get("user_id")
    return [], {}, None


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

    set_fields: Dict[str, Any] = {
        "extracted_constraints": constraints,
        "state_checkpoint": checkpoint,
        "updated_at": now,
    }
    if user_id:
        set_fields["user_id"] = user_id

    await db["user_sessions"].update_one(
        {"_id": session_id},
        {
            "$setOnInsert": {"created_at": now},
            "$push": {
                "conversation_history": {
                    "$each": [user_entry, bot_entry],
                    "$slice": -100
                }
            },
            "$set": set_fields
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
        "data": json.dumps({"event": "typing", "status": "thinking", "session_id": session_id})
    }
    await asyncio.sleep(0.05)

    # 2. Execute state machine turn in worker thread
    loop = asyncio.get_running_loop()
    try:
        result_state = await loop.run_in_executor(
            None,
            run_matchmaker_turn,
            session_id,
            user_message,
            history,
            prior_constraints
        )
    except Exception:
        logger.exception("Chat turn failed for session %s.", session_id)
        yield {
            "event": "error",
            "data": json.dumps({
                "event": "error",
                "message": "The chat service could not process this message.",
                "session_id": session_id
            })
        }
        return

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
            "data": json.dumps({"event": "token", "token": chunk, "session_id": session_id})
        }
        await asyncio.sleep(0.02)  # Natural typing rhythm

    # 4. If quick replies exist, emit quick-reply chips
    if quick_replies:
        yield {
            "event": "quick_replies",
            "data": json.dumps({"event": "quick_replies", "quick_replies": quick_replies, "options": quick_replies, "session_id": session_id})
        }

    # 5. If matches are found, emit matches and evaluations
    if is_complete and (candidates or evaluations):
        yield {
            "event": "matches",
            "data": json.dumps({
                "event": "matches",
                "candidate_matches": candidates,
                "matches": candidates,
                "evaluations": evaluations,
                "session_id": session_id
            })
        }

    try:
        await _save_session_data(
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            bot_message=response_text,
            constraints=updated_constraints,
            checkpoint={"is_complete": is_complete}
        )
    except Exception:
        logger.exception("Could not save chat session %s.", session_id)
        yield {
            "event": "error",
            "data": json.dumps({
                "event": "error",
                "message": "The response could not be saved. Please try again.",
                "session_id": session_id
            })
        }
        return

    # Emit done only after the response and updated state have been persisted.
    yield {
        "event": "done",
        "data": json.dumps({
            "event": "done",
            "session_id": session_id,
            "is_complete": is_complete,
            "response_message": response_text
        })
    }


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
    history, prior_constraints, session_user_id = await _load_session_data(request_data.session_id)

    if session_user_id and request_data.user_id and session_user_id != request_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This chat session belongs to a different user."
        )

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
    try:
        result_state = await loop.run_in_executor(
            None,
            run_matchmaker_turn,
            request_data.session_id,
            request_data.message,
            history,
            prior_constraints
        )
    except Exception:
        logger.exception("Chat turn failed for session %s.", request_data.session_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The chat service could not process this message."
        )

    response_text = result_state.get("response_message", "")
    updated_constraints = result_state.get("extracted_constraints", prior_constraints)

    try:
        await _save_session_data(
            session_id=request_data.session_id,
            user_id=request_data.user_id,
            user_message=request_data.message,
            bot_message=response_text,
            constraints=updated_constraints,
            checkpoint={"is_complete": result_state.get("is_complete", False)}
        )
    except Exception:
        logger.exception("Could not save chat session %s.", request_data.session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The response could not be saved. Please try again."
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
