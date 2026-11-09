"""
User Profile and Saved Pets (Favorites) endpoints.
[FROM MARKDOWN] matches Step 3.2: GET /api/v1/users/{id}/saved-pets and POST /api/v1/users/{id}/favorite/{petId}.
"""

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.database.connection import get_async_db
from app.models.user_profile import UserProfile
from app.models.pet import Pet

router = APIRouter(prefix="/users", tags=["Users"])


class FavoriteToggleResponse(BaseModel):
    user_id: str
    pet_id: str
    is_favorited: bool
    saved_pets_count: int


class UserProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    housing_type: Optional[str] = None
    has_children: Optional[bool] = None
    has_other_pets: Optional[bool] = None
    energy_budget: Optional[int] = Field(None, ge=1, le=5)


async def _get_or_create_user(user_id: str) -> dict:
    """Helper to retrieve or initialize a UserProfile document."""
    db = get_async_db()
    user_doc = await db["user_profiles"].find_one({"_id": user_id})
    if not user_doc:
        default_user = UserProfile(
            id=user_id,
            name="PawFect Adopter",
            email=f"{user_id}@pawfect.app",
            saved_pets=[]
        )
        await db["user_profiles"].insert_one(default_user.model_dump(by_alias=True))
        user_doc = default_user.model_dump(by_alias=True)
    return user_doc


@router.get("/{id}/profile", response_model=UserProfile, summary="Get User Profile")
async def get_user_profile(id: str):
    """
    Fetches user profile details for Profile Hub (Screen 8).
    """
    user_doc = await _get_or_create_user(id)
    return UserProfile(**user_doc)


@router.put("/{id}/profile", response_model=UserProfile, summary="Update User Profile")
async def update_user_profile(id: str, updates: UserProfileUpdateRequest):
    """
    Updates user lifestyle profile baseline and preferences.
    """
    db = get_async_db()
    await _get_or_create_user(id)

    update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc)

    await db["user_profiles"].update_one(
        {"_id": id},
        {"$set": update_dict}
    )

    updated_doc = await db["user_profiles"].find_one({"_id": id})
    return UserProfile(**updated_doc)


@router.get("/{id}/saved-pets", response_model=List[Pet], summary="Get User's Saved/Favorite Pets")
async def get_saved_pets(id: str):
    """
    [FROM MARKDOWN: Step 3.2 & Section 4]
    GET /api/v1/users/{id}/saved-pets
    Returns list of Pet documents saved/favorited by the user.
    """
    db = get_async_db()
    user_doc = await _get_or_create_user(id)
    saved_ids = user_doc.get("saved_pets", [])

    if not saved_ids:
        return []

    cursor = db["pets"].find({"_id": {"$in": saved_ids}})
    pet_docs = await cursor.to_list(length=100)
    return [Pet(**p) for p in pet_docs]


@router.post("/{id}/favorite/{petId}", response_model=FavoriteToggleResponse, summary="Toggle Pet Favorite Status")
async def toggle_favorite_pet(id: str, petId: str):
    """
    [FROM MARKDOWN: Step 3.2]
    POST /api/v1/users/{id}/favorite/{petId}
    Toggles a pet in the user's saved favorites list (heart button in Match Card / Pet Profile).
    """
    db = get_async_db()

    # Verify target pet exists
    pet_doc = await db["pets"].find_one({"_id": petId})
    if not pet_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pet with ID '{petId}' not found."
        )

    user_doc = await _get_or_create_user(id)
    saved_pets = user_doc.get("saved_pets", [])

    if petId in saved_pets:
        # Remove from favorites
        await db["user_profiles"].update_one(
            {"_id": id},
            {
                "$pull": {"saved_pets": petId},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            }
        )
        is_fav = False
        saved_pets.remove(petId)
    else:
        # Add to favorites
        await db["user_profiles"].update_one(
            {"_id": id},
            {
                "$addToSet": {"saved_pets": petId},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            }
        )
        is_fav = True
        saved_pets.append(petId)

    return FavoriteToggleResponse(
        user_id=id,
        pet_id=petId,
        is_favorited=is_fav,
        saved_pets_count=len(saved_pets)
    )

