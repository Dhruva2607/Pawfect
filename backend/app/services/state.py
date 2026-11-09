"""
LangGraph state definitions and structured constraint schemas.
[FROM MARKDOWN] matches Step 2.1: State Definition (MatchmakerState).
"""

from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field


class LifestyleConstraints(BaseModel):
    """
    Structured lifestyle parameters extracted from unstructured conversation.
    [FROM MARKDOWN: Step 2.1 & Step 2.2]
    """
    species: Optional[str] = Field(None, description="Preferred species: 'dog', 'cat', or 'any'")
    housing_type: Optional[str] = Field(None, description="'apartment', 'house_with_yard', or 'apartment_or_house'")
    has_children: Optional[bool] = Field(None, description="Whether children live in the household")
    has_other_pets: Optional[bool] = Field(None, description="Whether other resident pets live in the household")
    energy_budget: Optional[int] = Field(None, ge=1, le=5, description="Adopter energy budget / activity level (1 to 5)")
    allergies: Optional[bool] = Field(None, description="Whether adopter or family members have pet allergies (hypoallergenic requirement)")
    daily_alone_hours: Optional[int] = Field(None, description="Estimated hours pet would spend alone each day")
    notes: Optional[str] = Field(None, description="Any other lifestyle nuances mentioned by adopter")


class MatchmakerState(TypedDict, total=False):
    """
    LangGraph State Machine representation for AI Pet Matchmaker.
    [FROM MARKDOWN: Step 2.1]
    Contains: conversation history, extracted constraints, search queries, candidate matches, and evaluations.
    """
    session_id: str
    conversation_history: List[Dict[str, str]]
    user_message: str
    extracted_constraints: Dict[str, Any]
    search_queries: List[str]
    candidate_matches: List[Dict[str, Any]]
    evaluations: List[Dict[str, Any]]
    is_complete: bool
    response_message: str
    quick_replies: List[str]
    next_node: str

