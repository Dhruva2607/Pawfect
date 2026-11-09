"""
Pydantic v2 schema for Match Evaluation documents.
[FROM MARKDOWN] matches Step 1.1, Step 2.4 (0-100% score, exact pros, caveats).
"""

from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class MatchEvaluation(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id", description="Unique evaluation ID")
    session_id: str = Field(..., description="Related user session reference")
    pet_id: str = Field(..., description="Referenced Pet _id")
    compatibility_score: int = Field(..., ge=0, le=100, description="Compatibility percentage (0-100%)")
    pros: List[str] = Field(default_factory=list, description="Exact alignment points (e.g. 'Your activity level matches his energy')")
    caveats: List[str] = Field(default_factory=list, description="Potential lifestyle friction points or watch-outs")
    reasoning_summary: Optional[str] = Field(None, description="Concise narrative summary of evaluation")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True
    }

