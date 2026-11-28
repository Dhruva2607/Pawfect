"""
Meta endpoints for PawFect — exposes matching schema options.
The Android shelter form builds its dropdowns, chips, and sliders from
GET /meta/pet-options, never from hardcoded strings.
"""

from fastapi import APIRouter

from app.services.matching_schema import get_pet_options_response

router = APIRouter(prefix="/meta", tags=["Meta"])


@router.get("/pet-options")
async def pet_options():
    """
    Returns all matchable dimensions, allowed values, display labels,
    age-group ranges, alone-hours mapping, and housing normalization rules.

    The Android shelter form MUST build its UI from this endpoint.
    """
    return get_pet_options_response()
