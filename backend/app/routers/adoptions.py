"""
Adoption Application pipeline endpoints.
[FROM MARKDOWN] matches Step 3.2: POST /api/v1/adoptions/apply and GET /api/v1/adoptions/{id}/status.
Extended to copy shelter_id, snapshot applicant lifestyle & pet_name, compute
compatibility_score, record stage_history, and notify the owning shelter in real time.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.database.connection import get_async_db
from app.models.adoption_application import (
    AdoptionApplication,
    AdoptionStage,
    StageHistoryEntry,
)
from app.models.pet import Pet
from app.services.compatibility import evaluate_pet_compatibility
from app.services.notifications import create_notification

router = APIRouter(prefix="/adoptions", tags=["Adoptions"])


class AdoptionApplyRequest(BaseModel):
    user_id: str = Field(..., description="ID of applicant user")
    pet_id: str = Field(..., description="ID of target pet")
    applicant_name: str = Field(..., description="Full name of applicant")
    applicant_email: str = Field(..., description="Email address")
    applicant_phone: Optional[str] = Field(None, description="Phone number")
    housing_details: Optional[str] = Field(None, description="Apartment or house details, yard status")
    household_members: Optional[str] = Field(None, description="Children count, ages, other household pets")
    notes: Optional[str] = Field(None, description="Personal statement or message to shelter")


class AdoptionStatusResponse(BaseModel):
    application_id: str
    user_id: str
    pet_id: str
    pet_name: Optional[str] = None
    shelter_id: Optional[str] = None
    stage_status: AdoptionStage
    applicant_name: str
    shelter_note: Optional[str] = None
    compatibility_score: Optional[int] = None
    compatibility_reasoning: Optional[str] = None
    stage_history: List[StageHistoryEntry] = Field(default_factory=list)
    submitted_at: datetime
    updated_at: datetime


async def _snapshot_applicant_lifestyle(db: Any, user_doc: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    lifestyle: Dict[str, Any] = {
        "housing_type": user_doc.get("housing_type"),
        "has_children": user_doc.get("has_children"),
        "has_other_pets": user_doc.get("has_other_pets"),
        "energy_budget": user_doc.get("energy_budget"),
    }
    try:
        sessions_col = db["user_sessions"]
        if hasattr(sessions_col, "find_one"):
            session_doc = await sessions_col.find_one(
                {"user_id": user_id},
                sort=[("updated_at", -1)],
            )
            if session_doc and isinstance(session_doc.get("extracted_constraints"), dict):
                for k, v in session_doc["extracted_constraints"].items():
                    if v is not None and (k not in lifestyle or lifestyle[k] is None):
                        lifestyle[k] = v
    except (KeyError, TypeError):
        pass
    return {k: v for k, v in lifestyle.items() if v is not None}


def _app_doc_to_status_response(app_doc: Dict[str, Any], pet_name: Optional[str]) -> AdoptionStatusResponse:
    return AdoptionStatusResponse(
        application_id=app_doc["_id"],
        user_id=app_doc["user_id"],
        pet_id=app_doc["pet_id"],
        pet_name=pet_name or app_doc.get("pet_name"),
        shelter_id=app_doc.get("shelter_id"),
        stage_status=app_doc["stage_status"],
        applicant_name=app_doc["applicant_name"],
        shelter_note=app_doc.get("shelter_note"),
        compatibility_score=app_doc.get("compatibility_score"),
        compatibility_reasoning=app_doc.get("compatibility_reasoning"),
        stage_history=[StageHistoryEntry(**h) for h in (app_doc.get("stage_history") or [])],
        submitted_at=app_doc["submitted_at"],
        updated_at=app_doc["updated_at"],
    )


@router.post("/apply", response_model=AdoptionStatusResponse, status_code=status.HTTP_201_CREATED, summary="Submit Adoption Application")
async def apply_adoption(request: AdoptionApplyRequest):
    """
    [FROM MARKDOWN: Step 3.2 & Section 4]
    POST /api/v1/adoptions/apply
    Submits a new pet adoption application and initiates the Adoption Stepper.
    Copies shelter_id, snapshots lifestyle, computes compatibility score, and
    notifies the owning shelter.
    """
    db = get_async_db()

    user_doc = await db["user_profiles"].find_one({"_id": request.user_id})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{request.user_id}' does not exist."
        )

    pet_doc = await db["pets"].find_one({"_id": request.pet_id})
    if not pet_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pet with ID '{request.pet_id}' does not exist."
        )

    pet = Pet(**pet_doc)
    if pet_doc.get("status") not in (None, "available"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{pet.name} is currently '{pet_doc.get('status')}' and not accepting new applications.",
        )

    existing_app = await db["adoption_applications"].find_one({
        "user_id": request.user_id,
        "pet_id": request.pet_id
    })
    if existing_app:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You have already submitted an adoption application for {pet.name}."
        )

    now = datetime.now(timezone.utc)
    timestamp_str = now.strftime("%Y%m%d%H%M%S%f")
    app_id = f"app_{request.user_id}_{pet.id}_{timestamp_str}"

    lifestyle_snapshot = await _snapshot_applicant_lifestyle(db, user_doc, request.user_id)
    eval_result = await evaluate_pet_compatibility(pet, lifestyle_snapshot, use_llm=True)

    shelter_id = pet_doc.get("shelter_id")
    app_record = AdoptionApplication(
        id=app_id,
        user_id=request.user_id,
        pet_id=pet.id,
        shelter_id=shelter_id,
        pet_name=pet.name,
        stage_status=AdoptionStage.APPLY,
        applicant_name=request.applicant_name,
        applicant_email=request.applicant_email,
        applicant_phone=request.applicant_phone,
        housing_details=request.housing_details,
        household_members=request.household_members,
        notes=request.notes,
        applicant_lifestyle=lifestyle_snapshot,
        compatibility_score=eval_result.compatibility_score,
        compatibility_reasoning=eval_result.reasoning_summary,
        stage_history=[
            StageHistoryEntry(
                stage=AdoptionStage.APPLY,
                timestamp=now,
                note="Application submitted",
            )
        ],
        submitted_at=now,
        updated_at=now,
    )

    await db["adoption_applications"].insert_one(app_record.model_dump(by_alias=True))

    if shelter_id:
        await create_notification(
            db,
            recipient_role="shelter",
            recipient_id=shelter_id,
            notif_type="new_application",
            title=f"New application for {pet.name}",
            message=f"{request.applicant_name} applied to adopt {pet.name} ({eval_result.compatibility_score}% match).",
            pet_id=pet.id,
            pet_name=pet.name,
            application_id=app_id,
            applicant_name=request.applicant_name,
        )

    return _app_doc_to_status_response(app_record.model_dump(by_alias=True), pet.name)


@router.get("/{id}/status", response_model=AdoptionStatusResponse, summary="Get Adoption Application Status")
async def get_adoption_status(id: str):
    """
    [FROM MARKDOWN: Step 3.2]
    GET /api/v1/adoptions/{id}/status
    Fetches the live stage status for an adoption application.
    """
    db = get_async_db()
    app_doc = await db["adoption_applications"].find_one({"_id": id})
    if not app_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Adoption application with ID '{id}' not found."
        )

    pet_name = app_doc.get("pet_name")
    if not pet_name:
        pet_doc = await db["pets"].find_one({"_id": app_doc.get("pet_id")})
        if pet_doc:
            pet_name = pet_doc.get("name")

    return _app_doc_to_status_response(app_doc, pet_name)


@router.get("/user/{user_id}/pet/{pet_id}", response_model=Optional[AdoptionStatusResponse], summary="Check User Application for Pet")
async def get_user_pet_application(user_id: str, pet_id: str):
    """
    Returns the user's existing adoption application for a specific pet, if any.
    Used by frontend to check if user has already submitted an application.
    """
    db = get_async_db()
    app_doc = await db["adoption_applications"].find_one({
        "user_id": user_id,
        "pet_id": pet_id
    })
    if not app_doc:
        return None

    pet_name = app_doc.get("pet_name")
    if not pet_name:
        pet_doc = await db["pets"].find_one({"_id": app_doc.get("pet_id")})
        if pet_doc:
            pet_name = pet_doc.get("name")

    return _app_doc_to_status_response(app_doc, pet_name)
