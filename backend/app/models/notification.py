"""
Pydantic v2 schema for Notifications (shelter and adopter real-time alerts).
"""

from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, Field

RecipientRole = Literal["shelter", "adopter"]


class Notification(BaseModel):
    id: str = Field(alias="_id")
    recipient_role: RecipientRole
    recipient_id: str
    type: str
    title: str
    message: str
    pet_id: Optional[str] = None
    pet_name: Optional[str] = None
    application_id: Optional[str] = None
    applicant_name: Optional[str] = None
    read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
    }


class NotificationResponse(Notification):
    pass
