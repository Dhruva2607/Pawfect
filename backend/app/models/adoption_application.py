"""
Pydantic v2 schema for Adoption Application documents.
[FROM MARKDOWN] matches Step 1.1 and Step 3.2 (4-stage status: Match -> Review -> Apply -> Adopt).
"""

from typing import Optional
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field


class AdoptionStage(str, Enum):
    MATCH = "match"
    REVIEW = "review"
    APPLY = "apply"
    ADOPT = "adopt"


class AdoptionApplication(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id", description="Application ID")
    user_id: str = Field(..., description="Reference to user profile ID")
    pet_id: str = Field(..., description="Reference to pet _id")
    stage_status: AdoptionStage = Field(default=AdoptionStage.APPLY, description="4-stage stepper state")
    applicant_name: str = Field(..., description="Applicant contact name")
    applicant_email: str = Field(..., description="Applicant contact email")
    applicant_phone: Optional[str] = Field(None, description="Applicant phone number")
    housing_details: Optional[str] = Field(None, description="Housing type and landlord approval notes")
    household_members: Optional[str] = Field(None, description="Household composition (adults, children, other pets)")
    notes: Optional[str] = Field(None, description="Additional adoption remarks")
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True
    }

