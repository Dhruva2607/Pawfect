"""
Shelter (Adoption Center) router:
- Auth: POST /shelters/auth/signup, POST /shelters/auth/login
- Profile: GET /shelters/me, PUT /shelters/me
- Pet CRUD: POST/GET/PUT/PATCH/DELETE under /shelters/me/pets
- Photo upload: POST /shelters/me/pets/{pet_id}/photo
- Embedding retry: POST /shelters/me/pets/{pet_id}/retry-embedding

Ownership is enforced on every route via get_current_shelter.
"""

from datetime import datetime, timezone
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

from app.database.connection import get_async_db
from app.models.adoption_application import AdoptionApplication, AdoptionStage, StageHistoryEntry
from app.models.pet import (
    PetCreateRequest,
    PetResponse,
    PetStatusUpdateRequest,
    PetStatusValue,
    PetUpdateRequest,
    validate_complete_for_available,
)
from app.models.shelter import (
    Shelter,
    ShelterAuthResponse,
    ShelterLoginRequest,
    ShelterResponse,
    ShelterSignupRequest,
    ShelterUpdateRequest,
)
from app.services.auth import (
    create_shelter_token,
    get_current_shelter,
    hash_password,
    verify_password,
)
from app.services.matching_schema import compute_age_group
from app.services.pet_embeddings import (
    EMBEDDING_RELEVANT_FIELDS,
    generate_pet_embedding_async,
)
from app.services.notifications import create_notification
from app.services.rate_limit import embedding_limiter, rate_limit, shelter_key
from app.services.storage import save_pet_photo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/shelters", tags=["Shelters"])


def _shelter_to_response(doc: Dict[str, Any]) -> ShelterResponse:
    clean = dict(doc)
    clean.pop("password_hash", None)
    return ShelterResponse(**clean)


def _enrich_pet_with_shelter(pet_doc: Dict[str, Any], shelter: Dict[str, Any]) -> PetResponse:
    enriched = dict(pet_doc)
    enriched["shelter_name"] = shelter.get("name")
    enriched["shelter_city"] = shelter.get("city")
    return PetResponse(**enriched)


# ── Shelter Auth & Profile ────────────────────────────────────────────

@router.post("/auth/signup", response_model=ShelterAuthResponse, status_code=status.HTTP_201_CREATED)
async def shelter_signup(payload: ShelterSignupRequest):
    """Register a new adoption center / shelter account and issue a signed JWT."""
    db = get_async_db()
    email_norm = payload.email.strip().lower()

    existing = await db["shelters"].find_one({"email": email_norm})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A shelter with email '{email_norm}' is already registered.",
        )

    now = datetime.now(timezone.utc)
    shelter_id = f"shelter_{uuid.uuid4().hex[:12]}"
    shelter = Shelter(
        _id=shelter_id,
        name=payload.name.strip(),
        email=email_norm,
        password_hash=hash_password(payload.password),
        contact_phone=payload.contact_phone.strip(),
        address=payload.address.strip(),
        city=payload.city.strip(),
        state=payload.state.strip(),
        country=payload.country.strip(),
        latitude=payload.latitude,
        longitude=payload.longitude,
        description=payload.description,
        logo_url=payload.logo_url,
        website=payload.website,
        operating_hours=payload.operating_hours,
        registration_number=payload.registration_number,
        verified=False,
        created_at=now,
        updated_at=now,
    )

    doc = shelter.model_dump(by_alias=True)
    await db["shelters"].insert_one(doc)
    token = create_shelter_token(shelter_id=shelter_id, email=email_norm)

    return ShelterAuthResponse(
        token=token,
        role="shelter",
        shelter=_shelter_to_response(doc),
    )


@router.post("/auth/login", response_model=ShelterAuthResponse)
async def shelter_login(payload: ShelterLoginRequest):
    """Authenticate a shelter with email + password and return a signed JWT."""
    db = get_async_db()
    email_norm = payload.email.strip().lower()

    shelter_doc = await db["shelters"].find_one({"email": email_norm})
    if not shelter_doc or not verify_password(payload.password, shelter_doc.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_shelter_token(shelter_id=shelter_doc["_id"], email=email_norm)
    return ShelterAuthResponse(
        token=token,
        role="shelter",
        shelter=_shelter_to_response(shelter_doc),
    )


@router.get("/me", response_model=ShelterResponse)
async def get_my_shelter(shelter: Dict[str, Any] = Depends(get_current_shelter)):
    """Get the authenticated shelter's profile."""
    return _shelter_to_response(shelter)


@router.put("/me", response_model=ShelterResponse)
async def update_my_shelter(
    payload: ShelterUpdateRequest,
    shelter: Dict[str, Any] = Depends(get_current_shelter),
):
    """Update the authenticated shelter's profile."""
    db = get_async_db()
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        return _shelter_to_response(shelter)

    updates["updated_at"] = datetime.now(timezone.utc)
    await db["shelters"].update_one({"_id": shelter["_id"]}, {"$set": updates})
    updated = await db["shelters"].find_one({"_id": shelter["_id"]})
    return _shelter_to_response(updated or {**shelter, **updates})


# ── Shelter Pet CRUD (Owner-only) ─────────────────────────────────────

async def _get_owned_pet_or_404(db: Any, shelter_id: str, pet_id: str) -> Dict[str, Any]:
    pet_doc = await db["pets"].find_one({"_id": pet_id})
    if not pet_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pet '{pet_id}' not found.",
        )
    if pet_doc.get("shelter_id") != shelter_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access or modify this pet.",
        )
    return pet_doc


@router.post("/me/pets", response_model=PetResponse, status_code=status.HTTP_201_CREATED)
async def create_shelter_pet(
    payload: PetCreateRequest,
    shelter: Dict[str, Any] = Depends(get_current_shelter),
):
    """
    Create a new pet listing owned by the authenticated shelter.
    - Server computes `age_group` from `age_months`.
    - Generates 768-dim embedding off the event loop.
    - If embedding generation fails on an 'available' pet, marks `embedding_pending=True`
      and sets `status='hidden'` so no available pet is invisible to vector search.
    """
    db = get_async_db()
    now = datetime.now(timezone.utc)

    # Idempotency: the Android client sets retryOnConnectionFailure, which can
    # replay a POST after a network blip. A client-supplied key collapses those
    # retries onto one listing instead of silently creating duplicates.
    if payload.client_request_id:
        existing = await db["pets"].find_one({
            "shelter_id": shelter["_id"],
            "client_request_id": payload.client_request_id,
        })
        if existing:
            logger.info(
                "Reusing pet %s for repeated client_request_id %s",
                existing.get("_id"),
                payload.client_request_id,
            )
            return _enrich_pet_with_shelter(existing, shelter)

    pet_id = f"pet_{payload.species}_{uuid.uuid4().hex[:10]}"

    pet_data = payload.model_dump()
    pet_data["_id"] = pet_id
    pet_data["shelter_id"] = shelter["_id"]
    pet_data["age_group"] = compute_age_group(payload.age_months)
    pet_data["listed_at"] = now
    pet_data["updated_at"] = now

    if payload.status != "draft":
        vector, pending = await generate_pet_embedding_async(pet_data)
        pet_data["embedding"] = vector
        pet_data["embedding_pending"] = pending
        if pending:
            pet_data["status"] = "hidden"
    else:
        pet_data["embedding"] = None
        pet_data["embedding_pending"] = True

    await db["pets"].insert_one(pet_data)
    return _enrich_pet_with_shelter(pet_data, shelter)


@router.get("/me/pets", response_model=List[PetResponse])
async def list_my_shelter_pets(
    status_filter: Optional[PetStatusValue] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    shelter: Dict[str, Any] = Depends(get_current_shelter),
):
    """List pets owned by the authenticated shelter with optional status filter & pagination."""
    db = get_async_db()
    query: Dict[str, Any] = {"shelter_id": shelter["_id"]}
    if status_filter:
        query["status"] = status_filter

    cursor = db["pets"].find(query).sort("updated_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [_enrich_pet_with_shelter(d, shelter) for d in docs]


@router.get("/me/pets/{pet_id}", response_model=PetResponse)
async def get_my_shelter_pet(
    pet_id: str,
    shelter: Dict[str, Any] = Depends(get_current_shelter),
):
    """Get a single pet owned by the authenticated shelter."""
    db = get_async_db()
    pet_doc = await _get_owned_pet_or_404(db, shelter["_id"], pet_id)
    return _enrich_pet_with_shelter(pet_doc, shelter)


@router.put("/me/pets/{pet_id}", response_model=PetResponse)
async def update_my_shelter_pet(
    pet_id: str,
    payload: PetUpdateRequest,
    shelter: Dict[str, Any] = Depends(get_current_shelter),
):
    """
    Update a pet owned by the authenticated shelter.
    Recomputes `age_group` if `age_months` changed, validates completeness if
    target status is 'available', and regenerates embedding when any
    embedding-relevant field changes.
    """
    db = get_async_db()
    existing = await _get_owned_pet_or_404(db, shelter["_id"], pet_id)

    updates = payload.model_dump(exclude_none=True)
    if not updates:
        return _enrich_pet_with_shelter(existing, shelter)

    merged = {**existing, **updates}
    if "age_months" in updates:
        merged["age_group"] = compute_age_group(merged["age_months"])
        updates["age_group"] = merged["age_group"]

    target_status = merged.get("status", "available")
    if target_status == "available":
        try:
            validate_complete_for_available(merged)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e),
            )

    needs_reembed = bool(set(updates.keys()) & EMBEDDING_RELEVANT_FIELDS) or (
        target_status == "available" and not existing.get("embedding")
    )
    if needs_reembed and target_status != "draft":
        vector, pending = await generate_pet_embedding_async(merged)
        updates["embedding"] = vector
        updates["embedding_pending"] = pending
        if pending and target_status == "available":
            updates["status"] = "hidden"

    updates["updated_at"] = datetime.now(timezone.utc)
    await db["pets"].update_one({"_id": pet_id}, {"$set": updates})
    updated_doc = await db["pets"].find_one({"_id": pet_id})
    return _enrich_pet_with_shelter(updated_doc or {**merged, **updates}, shelter)


@router.patch("/me/pets/{pet_id}/status", response_model=PetResponse)
async def update_my_shelter_pet_status(
    pet_id: str,
    payload: PetStatusUpdateRequest,
    shelter: Dict[str, Any] = Depends(get_current_shelter),
):
    """Change the status of an owned pet (validates completeness before 'available')."""
    db = get_async_db()
    existing = await _get_owned_pet_or_404(db, shelter["_id"], pet_id)

    updates: Dict[str, Any] = {
        "status": payload.status,
        "updated_at": datetime.now(timezone.utc),
    }

    if payload.status == "available":
        try:
            validate_complete_for_available(existing)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e),
            )
        if not existing.get("embedding") or existing.get("embedding_pending"):
            vector, pending = await generate_pet_embedding_async(existing)
            updates["embedding"] = vector
            updates["embedding_pending"] = pending
            if pending:
                updates["status"] = "hidden"

    await db["pets"].update_one({"_id": pet_id}, {"$set": updates})
    updated_doc = await db["pets"].find_one({"_id": pet_id})
    return _enrich_pet_with_shelter(updated_doc or {**existing, **updates}, shelter)


@router.delete("/me/pets/{pet_id}", response_model=PetResponse)
async def soft_delete_my_shelter_pet(
    pet_id: str,
    shelter: Dict[str, Any] = Depends(get_current_shelter),
):
    """
    Soft-delete an owned pet by setting status='hidden' (or keeping 'adopted').
    Never hard-deletes pets, preserving adoption application history.
    """
    db = get_async_db()
    existing = await _get_owned_pet_or_404(db, shelter["_id"], pet_id)
    new_status = "adopted" if existing.get("status") == "adopted" else "hidden"
    updates = {"status": new_status, "updated_at": datetime.now(timezone.utc)}
    await db["pets"].update_one({"_id": pet_id}, {"$set": updates})
    updated_doc = await db["pets"].find_one({"_id": pet_id})
    return _enrich_pet_with_shelter(updated_doc or {**existing, **updates}, shelter)



@router.post("/me/pets/{pet_id}/photo")
async def upload_pet_photo(
    pet_id: str,
    file: UploadFile = File(...),
    shelter: Dict[str, Any] = Depends(get_current_shelter),
):
    """Upload a pet photo (JPEG/PNG/WebP, max 5MB) and update `photo_url`."""
    db = get_async_db()
    await _get_owned_pet_or_404(db, shelter["_id"], pet_id)
    photo_url = await save_pet_photo(pet_id, file)
    await db["pets"].update_one(
        {"_id": pet_id},
        {"$set": {"photo_url": photo_url, "updated_at": datetime.now(timezone.utc)}},
    )
    return {"pet_id": pet_id, "photo_url": photo_url}


@router.post("/me/pets/{pet_id}/retry-embedding", response_model=PetResponse)
async def retry_pet_embedding(
    pet_id: str,
    make_available: bool = Query(True),
    shelter: Dict[str, Any] = Depends(get_current_shelter),
):
    """Retry embedding generation for a pet whose embedding previously failed."""
    rate_limit(embedding_limiter, shelter_key(shelter["_id"], "embedding"))

    db = get_async_db()
    existing = await _get_owned_pet_or_404(db, shelter["_id"], pet_id)
    vector, pending = await generate_pet_embedding_async(existing)
    if pending or not vector:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding generation failed again. Please retry shortly.",
        )

    updates: Dict[str, Any] = {
        "embedding": vector,
        "embedding_pending": False,
        "updated_at": datetime.now(timezone.utc),
    }
    if make_available:
        try:
            validate_complete_for_available(existing)
            updates["status"] = "available"
        except ValueError:
            pass

    await db["pets"].update_one({"_id": pet_id}, {"$set": updates})
    updated_doc = await db["pets"].find_one({"_id": pet_id})
    return _enrich_pet_with_shelter(updated_doc or {**existing, **updates}, shelter)


# ── Shelter Applications & Dashboard Stats ────────────────────────────

_ALLOWED_STAGE_TRANSITIONS: Dict[str, set[str]] = {
    AdoptionStage.APPLY.value: {AdoptionStage.REVIEW.value, AdoptionStage.REJECTED.value},
    AdoptionStage.REVIEW.value: {AdoptionStage.ADOPT.value, AdoptionStage.REJECTED.value},
    AdoptionStage.ADOPT.value: set(),
    AdoptionStage.REJECTED.value: set(),
}


class ShelterStageUpdateRequest(BaseModel):
    stage_status: AdoptionStage
    shelter_note: Optional[str] = Field(None, max_length=1000)


class ShelterStatsResponse(BaseModel):
    available_pets: int
    pending_pets: int
    adopted_pets: int
    total_pets: int
    new_applications: int
    in_review: int
    adopted_applications: int
    rejected_applications: int
    unread_notifications: int


async def _get_owned_application_or_404(db: Any, shelter_id: str, app_id: str) -> Dict[str, Any]:
    app_doc = await db["adoption_applications"].find_one({"_id": app_id})
    if not app_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application '{app_id}' not found.",
        )
    if app_doc.get("shelter_id") != shelter_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this application.",
        )
    return app_doc


@router.get("/me/applications", response_model=List[AdoptionApplication])
async def list_my_shelter_applications(
    stage_status: Optional[AdoptionStage] = Query(None, alias="status"),
    pet_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    shelter: Dict[str, Any] = Depends(get_current_shelter),
):
    """List adoption applications for pets owned by the authenticated shelter."""
    db = get_async_db()
    query: Dict[str, Any] = {"shelter_id": shelter["_id"]}
    if stage_status:
        query["stage_status"] = stage_status.value
    if pet_id:
        query["pet_id"] = pet_id

    cursor = db["adoption_applications"].find(query).sort("submitted_at", -1)
    if skip > 0 and hasattr(cursor, "skip"):
        cursor = cursor.skip(skip)
    cursor = cursor.limit(limit)
    docs = await cursor.to_list(length=limit)
    return [AdoptionApplication(**d) for d in docs]


@router.get("/me/applications/{app_id}", response_model=AdoptionApplication)
async def get_my_shelter_application(
    app_id: str,
    shelter: Dict[str, Any] = Depends(get_current_shelter),
):
    """Get full applicant details & compatibility score for an owned application."""
    db = get_async_db()
    app_doc = await _get_owned_application_or_404(db, shelter["_id"], app_id)
    return AdoptionApplication(**app_doc)


@router.patch("/me/applications/{app_id}/stage", response_model=AdoptionApplication)
async def update_application_stage(
    app_id: str,
    payload: ShelterStageUpdateRequest,
    shelter: Dict[str, Any] = Depends(get_current_shelter),
):
    """
    Advance or reject an adoption application (apply -> review -> adopt, or -> rejected).
    Side effects:
    - Appends to stage_history and updates shelter_note.
    - Notifies the adopter about the status change.
    - When reaching 'adopt', sets the pet status to 'adopted' and auto-declines
      all other open applications for that pet with notifications.
    """
    db = get_async_db()
    app_doc = await _get_owned_application_or_404(db, shelter["_id"], app_id)

    current_stage = app_doc.get("stage_status", AdoptionStage.APPLY.value)
    target_stage = payload.stage_status.value
    allowed = _ALLOWED_STAGE_TRANSITIONS.get(current_stage, set())
    if target_stage not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid stage transition from '{current_stage}' to '{target_stage}'.",
        )

    now = datetime.now(timezone.utc)
    history = list(app_doc.get("stage_history") or [])
    history.append(
        StageHistoryEntry(
            stage=payload.stage_status,
            timestamp=now,
            note=payload.shelter_note,
        ).model_dump()
    )

    updates: Dict[str, Any] = {
        "stage_status": target_stage,
        "stage_history": history,
        "updated_at": now,
    }
    if payload.shelter_note is not None:
        updates["shelter_note"] = payload.shelter_note

    await db["adoption_applications"].update_one({"_id": app_id}, {"$set": updates})

    pet_id = app_doc["pet_id"]
    pet_name = app_doc.get("pet_name") or "your pet"

    # Notify adopter of stage update
    await create_notification(
        db,
        recipient_role="adopter",
        recipient_id=app_doc["user_id"],
        notif_type="application_stage_changed",
        title=f"Application update for {pet_name}",
        message=(
            f"Your adoption application for {pet_name} is now '{target_stage}'."
            + (f" Note: {payload.shelter_note}" if payload.shelter_note else "")
        ),
        pet_id=pet_id,
        pet_name=pet_name,
        application_id=app_id,
        applicant_name=app_doc.get("applicant_name"),
    )

    # Side effects on 'adopt': mark pet adopted + auto-decline other open applications
    if target_stage == AdoptionStage.ADOPT.value:
        await db["pets"].update_one(
            {"_id": pet_id},
            {"$set": {"status": "adopted", "updated_at": now}},
        )

        other_cursor = db["adoption_applications"].find({
            "pet_id": pet_id,
            "_id": {"$ne": app_id},
            "stage_status": {"$in": [AdoptionStage.APPLY.value, AdoptionStage.REVIEW.value]},
        })
        other_apps = await other_cursor.to_list(length=200)
        auto_decline_note = f"{pet_name} has been adopted by another applicant."
        for other in other_apps:
            other_history = list(other.get("stage_history") or [])
            other_history.append(
                StageHistoryEntry(
                    stage=AdoptionStage.REJECTED,
                    timestamp=now,
                    note=auto_decline_note,
                ).model_dump()
            )
            await db["adoption_applications"].update_one(
                {"_id": other["_id"]},
                {
                    "$set": {
                        "stage_status": AdoptionStage.REJECTED.value,
                        "shelter_note": auto_decline_note,
                        "stage_history": other_history,
                        "updated_at": now,
                    }
                },
            )
            await create_notification(
                db,
                recipient_role="adopter",
                recipient_id=other["user_id"],
                notif_type="application_auto_declined",
                title=f"Update on {pet_name}",
                message=auto_decline_note,
                pet_id=pet_id,
                pet_name=pet_name,
                application_id=other["_id"],
                applicant_name=other.get("applicant_name"),
            )

    updated_doc = await db["adoption_applications"].find_one({"_id": app_id})
    return AdoptionApplication(**(updated_doc or {**app_doc, **updates}))


@router.get("/me/stats", response_model=ShelterStatsResponse)
async def get_my_shelter_stats(shelter: Dict[str, Any] = Depends(get_current_shelter)):
    """Return dashboard counts for the authenticated shelter."""
    db = get_async_db()
    sid = shelter["_id"]

    available_pets = await db["pets"].count_documents({"shelter_id": sid, "status": "available"})
    pending_pets = await db["pets"].count_documents({"shelter_id": sid, "status": "pending"})
    adopted_pets = await db["pets"].count_documents({"shelter_id": sid, "status": "adopted"})
    total_pets = await db["pets"].count_documents({"shelter_id": sid})

    new_apps = await db["adoption_applications"].count_documents(
        {"shelter_id": sid, "stage_status": AdoptionStage.APPLY.value}
    )
    in_review = await db["adoption_applications"].count_documents(
        {"shelter_id": sid, "stage_status": AdoptionStage.REVIEW.value}
    )
    adopted_apps = await db["adoption_applications"].count_documents(
        {"shelter_id": sid, "stage_status": AdoptionStage.ADOPT.value}
    )
    rejected_apps = await db["adoption_applications"].count_documents(
        {"shelter_id": sid, "stage_status": AdoptionStage.REJECTED.value}
    )

    unread_notifs = 0
    try:
        unread_notifs = await db["notifications"].count_documents(
            {"recipient_role": "shelter", "recipient_id": sid, "read": False}
        )
    except (KeyError, TypeError):
        pass

    return ShelterStatsResponse(
        available_pets=available_pets,
        pending_pets=pending_pets,
        adopted_pets=adopted_pets,
        total_pets=total_pets,
        new_applications=new_apps,
        in_review=in_review,
        adopted_applications=adopted_apps,
        rejected_applications=rejected_apps,
        unread_notifications=unread_notifs,
    )
