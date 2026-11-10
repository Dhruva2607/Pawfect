"""
Adoption Application pipeline endpoints.
[FROM MARKDOWN] matches Step 3.2: POST /api/v1/adoptions/apply and GET /api/v1/adoptions/{id}/status.
"""

from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.database.connection import get_async_db
from app.models.adoption_application import AdoptionApplication, AdoptionStage
from app.models.pet import Pet

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
    stage_status: AdoptionStage
    applicant_name: str
    submitted_at: datetime
    updated_at: datetime


@router.post("/apply", response_model=AdoptionStatusResponse, status_code=status.HTTP_201_CREATED, summary="Submit Adoption Application")
async def apply_adoption(request: AdoptionApplyRequest):
    """
    [FROM MARKDOWN: Step 3.2 & Section 4]
    POST /api/v1/adoptions/apply
    Submits a new pet adoption application and initiates the 4-Stage Adoption Stepper (Match -> Review -> Apply -> Adopt).
    """
    db = get_async_db()

    # Verify the applicant user exists
    user_doc = await db["user_profiles"].find_one({"_id": request.user_id})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{request.user_id}' does not exist."
        )

    # Verify pet exists
    pet_doc = await db["pets"].find_one({"_id": request.pet_id})
    if not pet_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pet with ID '{request.pet_id}' does not exist."
        )

    pet = Pet(**pet_doc)

    # Generate custom application id
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    app_id = f"app_{request.user_id}_{pet.id}_{timestamp_str}"

    app_record = AdoptionApplication(
        id=app_id,
        user_id=request.user_id,
        pet_id=pet.id,
        stage_status=AdoptionStage.APPLY,
        applicant_name=request.applicant_name,
        applicant_email=request.applicant_email,
        applicant_phone=request.applicant_phone,
        housing_details=request.housing_details,
        household_members=request.household_members,
        notes=request.notes
    )

    await db["adoption_applications"].insert_one(app_record.model_dump(by_alias=True))

    return AdoptionStatusResponse(
        application_id=app_id,
        user_id=request.user_id,
        pet_id=pet.id,
        pet_name=pet.name,
        stage_status=app_record.stage_status,
        applicant_name=app_record.applicant_name,
        submitted_at=app_record.submitted_at,
        updated_at=app_record.updated_at
    )


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

    pet_name = None
    pet_doc = await db["pets"].find_one({"_id": app_doc.get("pet_id")})
    if pet_doc:
        pet_name = pet_doc.get("name")

    return AdoptionStatusResponse(
        application_id=app_doc["_id"],
        user_id=app_doc["user_id"],
        pet_id=app_doc["pet_id"],
        pet_name=pet_name,
        stage_status=app_doc["stage_status"],
        applicant_name=app_doc["applicant_name"],
        submitted_at=app_doc["submitted_at"],
        updated_at=app_doc["updated_at"]
    )

