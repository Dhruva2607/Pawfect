"""
Pet catalog endpoints.
[FROM MARKDOWN] matches Step 3.1: GET /api/v1/pets/{id} and pet listing for client views.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.database.connection import get_async_db
from app.models.pet import Pet

router = APIRouter(prefix="/pets", tags=["Pets"])


@router.get("", response_model=List[Pet], summary="List all available pets")
async def list_pets(
    species: Optional[str] = Query(None, description="Filter by species: dog, cat"),
    size: Optional[str] = Query(None, description="Filter by size: small, medium, large"),
    good_with_kids: Optional[bool] = Query(None, description="Filter pets safe for children"),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Fetches list of shelter pets with optional operational filters.
    Used by mobile app for Discover/Catalog and Matches views.
    """
    db = get_async_db()
    query = {}
    if species:
        query["species"] = species.lower()
    if size:
        query["size"] = size.lower()
    if good_with_kids is not None:
        query["good_with_kids"] = good_with_kids

    cursor = db["pets"].find(query).limit(limit)
    pets = await cursor.to_list(length=limit)
    return [Pet(**p) for p in pets]


@router.get("/{id}", response_model=Pet, summary="Get pet details by ID")
async def get_pet(id: str):
    """
    [FROM MARKDOWN: Step 3.1 & Section 4]
    Fetches static pet details (e.g. GET /pets/{id}) for Pet Detail Screen (Screen 5).
    """
    db = get_async_db()
    doc = await db["pets"].find_one({"_id": id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pet with ID '{id}' not found."
        )
    return Pet(**doc)

