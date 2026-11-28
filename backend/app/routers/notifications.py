"""
Notifications router for both shelters (JWT auth) and adopters (user_id / demo token).
Provides polling endpoints + real-time SSE stream.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Header, HTTPException, Query, status
from sse_starlette.sse import EventSourceResponse

from app.database.connection import get_async_db
from app.models.notification import NotificationResponse
from app.services.auth import decode_jwt_token
from app.services.notifications import notification_broker

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _resolve_recipient(
    authorization: Optional[str],
    user_id: Optional[str],
) -> Tuple[str, str]:
    """
    Resolve (recipient_role, recipient_id) from either:
    - Shelter JWT: Authorization: Bearer <jwt>
    - Adopter demo token: Authorization: Bearer token_<user_id>
    - Adopter query param: ?user_id=<user_id>
    """
    if authorization:
        parts = authorization.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip()
            if token.startswith("token_"):
                uid = token[len("token_"):]
                if uid:
                    return ("adopter", uid)
            payload = decode_jwt_token(token)
            if payload.get("role") == "shelter" and payload.get("shelter_id"):
                return ("shelter", payload["shelter_id"])

    if user_id:
        return ("adopter", user_id)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication or user_id required to access notifications.",
    )


@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(default=None),
):
    """List notifications for the authenticated shelter or adopter."""
    role, recipient_id = _resolve_recipient(authorization, user_id)
    db = get_async_db()

    query: Dict[str, Any] = {"recipient_role": role, "recipient_id": recipient_id}
    if unread_only:
        query["read"] = False

    cursor = db["notifications"].find(query).sort("created_at", -1)
    if skip > 0 and hasattr(cursor, "skip"):
        cursor = cursor.skip(skip)
    cursor = cursor.limit(limit)
    docs = await cursor.to_list(length=limit)
    return [NotificationResponse(**d) for d in docs]


@router.get("/unread-count")
async def get_unread_count(
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(default=None),
):
    """Return unread notification count for badge rendering."""
    role, recipient_id = _resolve_recipient(authorization, user_id)
    db = get_async_db()
    query = {"recipient_role": role, "recipient_id": recipient_id, "read": False}
    count = await db["notifications"].count_documents(query)
    return {"unread_count": count}


@router.patch("/{notif_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notif_id: str,
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(default=None),
):
    """Mark a single notification as read (owner-checked)."""
    role, recipient_id = _resolve_recipient(authorization, user_id)
    db = get_async_db()

    doc = await db["notifications"].find_one({"_id": notif_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    if doc.get("recipient_role") != role or doc.get("recipient_id") != recipient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your notification.")

    await db["notifications"].update_one({"_id": notif_id}, {"$set": {"read": True}})
    doc["read"] = True
    return NotificationResponse(**doc)


@router.post("/read-all")
async def mark_all_notifications_read(
    user_id: Optional[str] = Query(None),
    authorization: Optional[str] = Header(default=None),
):
    """Mark all notifications for the current recipient as read."""
    role, recipient_id = _resolve_recipient(authorization, user_id)
    db = get_async_db()
    await db["notifications"].update_many(
        {"recipient_role": role, "recipient_id": recipient_id, "read": False},
        {"$set": {"read": True}},
    )
    return {"status": "ok"}


@router.get("/stream")
async def stream_notifications(
    user_id: Optional[str] = Query(None),
    token: Optional[str] = Query(None, description="Optional JWT for EventSource clients that cannot set headers"),
    authorization: Optional[str] = Header(default=None),
):
    """Real-time SSE stream pushing new notifications for the authenticated shelter or adopter."""
    auth_header = authorization or (f"Bearer {token}" if token else None)
    role, recipient_id = _resolve_recipient(auth_header, user_id)
    queue = notification_broker.subscribe(role, recipient_id)

    async def event_generator():
        try:
            yield {"event": "connected", "data": json.dumps({"role": role, "recipient_id": recipient_id})}
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=25.0)
                    yield {"event": "notification", "data": json.dumps(payload)}
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": "{}"}
        finally:
            notification_broker.unsubscribe(role, recipient_id, queue)

    return EventSourceResponse(event_generator())
