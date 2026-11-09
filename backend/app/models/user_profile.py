"""
Pydantic v2 schema for User Profile documents.
[FROM MARKDOWN] matches Step 1.1 (favorites, user info) and Step 3.2.
"""

from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    id: str = Field(alias="_id", description="User ID")
    name: str = Field(..., description="Full user display name")
    email: str = Field(..., description="User email address")
    avatar_url: Optional[str] = Field(None, description="Profile avatar picture URL")
    housing_type: Optional[str] = Field(None, description="apartment, house_with_yard, etc.")
    has_children: Optional[bool] = Field(None, description="Whether user household includes children")
    has_other_pets: Optional[bool] = Field(None, description="Whether user already has resident pets")
    energy_budget: Optional[int] = Field(None, ge=1, le=5, description="Self-reported activity energy budget (1-5)")
    saved_pets: List[str] = Field(default_factory=list, description="List of favorited Pet _id references")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True
    }

