"""
Pydantic v2 schema for User Session documents.
[FROM MARKDOWN] matches Step 1.1 (user_sessions collection for LangGraph checkpoints/state).
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class UserSession(BaseModel):
    id: str = Field(alias="_id", description="Session ID / conversation ID")
    user_id: Optional[str] = Field(None, description="Associated user ID if authenticated")
    state_checkpoint: Dict[str, Any] = Field(default_factory=dict, description="LangGraph serialized state checkpoint")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="List of messages exchanged")
    extracted_constraints: Dict[str, Any] = Field(default_factory=dict, description="Extracted lifestyle parameters")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True
    }

