"""
Pydantic v2 schema for Adoption Application documents.
[FROM MARKDOWN] matches Step 1.1 and Step 3.2 (Match -> Review -> Apply -> Adopt + Rejected).
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AdoptionStage(str, Enum):
    MATCH = "match"
    REVIEW = "review"
    APPLY = "apply"
    ADOPT = "adopt"
    REJECTED = "rejected"


class StageHistoryEntry(BaseModel):
    stage: AdoptionStage
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    note: Optional[str] = None


class AdoptionApplication(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id", description="Application ID")
    user_id: str = Field(..., description="Reference to user profile ID")
    pet_id: str = Field(..., description="Reference to pet _id")
    shelter_id: Optional[str] = Field(default=None, description="Owning shelter ID copied from pet")
    pet_name: Optional[str] = Field(default=None, description="Snapshot of pet name")
    stage_status: AdoptionStage = Field(default=AdoptionStage.APPLY, description="Adoption stepper state")
    applicant_name: str = Field(..., description="Applicant contact name")
    applicant_email: str = Field(..., description="Applicant contact email")
    applicant_phone: Optional[str] = Field(None, description="Applicant phone number")
    housing_details: Optional[str] = Field(None, description="Housing type and landlord approval notes")
    household_members: Optional[str] = Field(None, description="Household composition (adults, children, other pets)")
    notes: Optional[str] = Field(None, description="Additional adoption remarks")
    applicant_lifestyle: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Snapshot of applicant lifestyle & chat-derived constraints",
    )
    compatibility_score: Optional[int] = Field(default=None, ge=0, le=100)
    compatibility_reasoning: Optional[str] = Field(default=None)
    shelter_note: Optional[str] = Field(default=None)
    stage_history: List[StageHistoryEntry] = Field(default_factory=list)
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True
    }
