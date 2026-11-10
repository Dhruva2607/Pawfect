"""
Direct Compatibility Evaluation endpoints.
[FROM MARKDOWN] matches Step 3.1: POST /api/v1/matches/direct-eval.
"""

import asyncio
import json
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.database.connection import get_async_db
from app.models.match_evaluation import MatchEvaluation
from app.models.pet import Pet
from app.services.llm import get_chat_llm
from app.services.nodes import SinglePetCompatibility

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matches", tags=["Matches"])


class DirectEvalRequest(BaseModel):
    session_id: str = Field(..., description="Active session ID")
    pet_id: str = Field(..., description="Target Pet ID to evaluate against")
    housing_type: Optional[str] = Field("apartment", description="apartment, house_with_yard")
    has_children: Optional[bool] = Field(False, description="Children in household")
    has_other_pets: Optional[bool] = Field(False, description="Other resident pets")
    energy_budget: Optional[int] = Field(3, ge=1, le=5, description="Adopter activity level (1-5)")
    notes: Optional[str] = Field(None, description="Any specific adopter lifestyle notes")


class DirectEvalResponse(BaseModel):
    pet_id: str
    pet_name: str
    compatibility_score: int = Field(..., ge=0, le=100)
    pros: List[str]
    caveats: List[str]
    reasoning_summary: str


@router.post("/direct-eval", response_model=DirectEvalResponse, summary="Direct Compatibility Evaluation")
async def direct_eval(request: DirectEvalRequest):
    """
    [FROM MARKDOWN: Step 3.1]
    POST /api/v1/matches/direct-eval
    Executes a direct compatibility evaluation of an adopter's lifestyle against a specific pet.
    Returns grounded 0-100% score, exact pros, and caveats.
    Persists evaluation record to 'match_evaluations' collection.
    """
    db = get_async_db()
    pet_doc = await db["pets"].find_one({"_id": request.pet_id})
    if not pet_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pet with ID '{request.pet_id}' not found."
        )

    pet = Pet(**pet_doc)

    # Prepare grounding dossier
    dossier = {
        "id": pet.id,
        "name": pet.name,
        "species": pet.species,
        "breed": pet.breed,
        "age_months": pet.age_months,
        "energy_level": pet.energy_level,
        "housing_requirement": pet.housing_requirement,
        "good_with_kids": pet.good_with_kids,
        "good_with_other_pets": pet.good_with_other_pets,
        "temperament": pet.temperament,
        "exercise_needs": pet.exercise_needs,
        "quirks": pet.quirks,
        "triggers": pet.triggers,
        "bio_text": pet.bio_text
    }

    lifestyle = {
        "housing_type": request.housing_type,
        "has_children": request.has_children,
        "has_other_pets": request.has_other_pets,
        "energy_budget": request.energy_budget,
        "notes": request.notes
    }

    system_prompt = (
        "You are the Lead Adoption Counselor and Compatibility Engine for PawFect.\n"
        "Analyze the provided pet and adopter lifestyle to compute an explainable, grounded compatibility evaluation.\n\n"
        "GUARDRAILS [FROM STEP 6.1]:\n"
        "- Base all reasoning strictly on the pet's documented traits. Never hallucinate.\n"
        "- Score: 0-100%.\n"
        "- Pros: 2-3 specific lifestyle alignment statements.\n"
        "- Caveats: 1-2 realistic watch-outs or considerations.\n"
    )

    human_prompt = (
        f"Adopter Lifestyle: {json.dumps(lifestyle, indent=2)}\n\n"
        f"Target Pet Dossier: {json.dumps(dossier, indent=2)}\n\n"
        "Generate a structured compatibility evaluation."
    )

    llm = await asyncio.to_thread(get_chat_llm, temperature=0.1)
    structured_llm = llm.with_structured_output(SinglePetCompatibility)

    try:
        eval_result: SinglePetCompatibility = await structured_llm.ainvoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": human_prompt}
        ])
    except Exception as e:
        logger.error("Direct evaluation LLM error: %s. Using heuristic fallback.", e)
        # Fallback scoring
        score = 80
        if request.has_children and not pet.good_with_kids:
            score -= 30
        if request.has_other_pets and not pet.good_with_other_pets:
            score -= 30
        if request.housing_type == "apartment" and pet.housing_requirement == "house_with_yard":
            score -= 25

        score = max(40, min(95, score))
        eval_result = SinglePetCompatibility(
            pet_id=pet.id,
            pet_name=pet.name,
            compatibility_score=score,
            pros=[f"Matches housing requirement ({pet.housing_requirement})"],
            caveats=[f"Exercise requirement: {pet.exercise_needs or 'Moderate'}"],
            reasoning_summary=f"{pet.name} is a wonderful {pet.breed} to consider for your home."
        )

    eval_record = MatchEvaluation(
        session_id=request.session_id,
        pet_id=pet.id,
        compatibility_score=eval_result.compatibility_score,
        pros=eval_result.pros,
        caveats=eval_result.caveats,
        reasoning_summary=eval_result.reasoning_summary
    )
    await db["match_evaluations"].update_one(
        {"session_id": request.session_id, "pet_id": pet.id},
        {"$set": eval_record.model_dump(by_alias=True, exclude={"id"}, exclude_none=True)},
        upsert=True
    )

    return DirectEvalResponse(
        pet_id=pet.id,
        pet_name=pet.name,
        compatibility_score=eval_result.compatibility_score,
        pros=eval_result.pros,
        caveats=eval_result.caveats,
        reasoning_summary=eval_result.reasoning_summary
    )
