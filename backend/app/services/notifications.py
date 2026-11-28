"""
Notification persistence + in-process SSE pub/sub broker.
"""

import asyncio
from datetime import datetime, timezone
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from app.models.notification import Notification, RecipientRole

logger = logging.getLogger(__name__)


class NotificationBroker:
    """In-memory pub/sub broker keyed by (recipient_role, recipient_id) for SSE streams."""

    def __init__(self) -> None:
        self._subscribers: Dict[Tuple[str, str], List[asyncio.Queue]] = {}

    def subscribe(self, role: str, recipient_id: str) -> asyncio.Queue:
        key = (role, recipient_id)
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.setdefault(key, []).append(queue)
        return queue

    def unsubscribe(self, role: str, recipient_id: str, queue: asyncio.Queue) -> None:
        key = (role, recipient_id)
        queues = self._subscribers.get(key, [])
        if queue in queues:
            queues.remove(queue)
        if not queues and key in self._subscribers:
            del self._subscribers[key]

    def publish(self, role: str, recipient_id: str, payload: Dict[str, Any]) -> None:
        key = (role, recipient_id)
        for queue in list(self._subscribers.get(key, [])):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                logger.warning("Notification queue full for %s; dropping live push.", key)


notification_broker = NotificationBroker()


async def create_notification(
    db: Any,
    *,
    recipient_role: RecipientRole,
    recipient_id: str,
    notif_type: str,
    title: str,
    message: str,
    pet_id: Optional[str] = None,
    pet_name: Optional[str] = None,
    application_id: Optional[str] = None,
    applicant_name: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Persist a notification to MongoDB and push it to any active SSE subscribers."""
    if not recipient_id:
        return None

    notif = Notification(
        _id=f"notif_{uuid.uuid4().hex[:12]}",
        recipient_role=recipient_role,
        recipient_id=recipient_id,
        type=notif_type,
        title=title,
        message=message,
        pet_id=pet_id,
        pet_name=pet_name,
        application_id=application_id,
        applicant_name=applicant_name,
        read=False,
        created_at=datetime.now(timezone.utc),
    )
    doc = notif.model_dump(by_alias=True)

    try:
        await db["notifications"].insert_one(doc)
    except (KeyError, TypeError):
        logger.debug("notifications collection not available on fake db; skipping insert.")
        return None

    # Push live over SSE broker (serialize datetime cleanly)
    live_payload = {
        **doc,
        "created_at": doc["created_at"].isoformat(),
    }
    notification_broker.publish(recipient_role, recipient_id, live_payload)
    return doc
