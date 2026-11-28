"""
Pet catalog endpoints.
[FROM MARKDOWN] matches Step 3.1: GET /api/v1/pets/{id} and pet listing for client views.
Extended to filter status='available' by default, support shelter_id, pagination,
updated_after, and enrich responses with shelter_name & shelter_city.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.database.connection import get_async_db
from app.models.pet import PetResponse

router = APIRouter(prefix="/pets", tags=["Pets"])


async def _load_shelter_map(db: Any, shelter_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Fetch shelter name/city for a batch of shelter IDs."""
    if not shelter_ids:
        return {}
    try:
        shelters_col = db["shelters"]
    except (KeyError, TypeError):
        return {}

    cursor = shelters_col.find({"_id": {"$in": shelter_ids}}, {"name": 1, "city": 1})
    docs = await cursor.to_list(length=len(shelter_ids))
    return {d["_id"]: d for d in docs if "_id" in d}


def _enrich_pet_response(doc: Dict[str, Any], shelter_map: Dict[str, Dict[str, Any]]) -> PetResponse:
    enriched = dict(doc)
    sid = enriched.get("shelter_id")
    if sid and sid in shelter_map:
        enriched["shelter_name"] = shelter_map[sid].get("name")
        enriched["shelter_city"] = shelter_map[sid].get("city")
    return PetResponse(**enriched)


@router.get(
    "",
    response_model=List[PetResponse],
    summary="List all available pets"
)
async def list_pets(
    species: Optional[str] = Query(None, description="Filter by species: dog, cat"),
    size: Optional[str] = Query(None, description="Filter by size: small, medium, large"),
    good_with_kids: Optional[bool] = Query(None, description="Filter pets safe for children"),
    shelter_id: Optional[str] = Query(None, description="Filter by owning shelter ID"),
    updated_after: Optional[datetime] = Query(None, description="Return pets updated after this ISO timestamp"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Pagination page size"),
):
    """
    Fetches list of available shelter pets with optional operational filters.
    Used by mobile app for Discover/Catalog and Matches views.
    """
    db = get_async_db()
    query: Dict[str, Any] = {"status": "available"}
    if species:
        query["species"] = species.lower()
    if size:
        query["size"] = size.lower()
    if good_with_kids is not None:
        query["good_with_kids"] = good_with_kids
    if shelter_id:
        query["shelter_id"] = shelter_id
    if updated_after is not None:
        query["updated_at"] = {"$gt": updated_after}

    cursor = db["pets"].find(query)
    if hasattr(cursor, "sort"):
        cursor = cursor.sort("listed_at", -1)
    if skip > 0 and hasattr(cursor, "skip"):
        cursor = cursor.skip(skip)
    cursor = cursor.limit(limit)
    pets = await cursor.to_list(length=limit)

    shelter_ids = list({p.get("shelter_id") for p in pets if p.get("shelter_id")})
    shelter_map = await _load_shelter_map(db, shelter_ids)
    return [_enrich_pet_response(p, shelter_map) for p in pets]


@router.get(
    "/{id}",
    response_model=PetResponse,
    summary="Get pet details by ID"
)
async def get_pet(id: str):
    """
    [FROM MARKDOWN: Step 3.1 & Section 4]
    Fetches static pet details (e.g. GET /pets/{id}) for Pet Detail Screen (Screen 5).
    Returns only available pets (unless adopted/hidden is not requested).
    """
    db = get_async_db()
    doc = await db["pets"].find_one({"_id": id, "status": "available"})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pet with ID '{id}' not found."
        )
    shelter_map = await _load_shelter_map(db, [doc["shelter_id"]] if doc.get("shelter_id") else [])
    return _enrich_pet_response(doc, shelter_map)
