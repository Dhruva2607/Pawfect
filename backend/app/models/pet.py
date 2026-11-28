"""
Pydantic v2 schema for Pet documents and shelter pet CRUD payloads.
[FROM MARKDOWN] matches Step 1.1, Step 1.3 and sample JSON in Section 5.
Extended backward-compatibly with shelter ownership, lifecycle status,
timestamps, hypoallergenic flag, health/ideal-adopter metadata, and
single-source-of-truth validation from matching_schema.py.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator

from app.services.matching_schema import (
    AloneToleranceValue,
    ExperienceValue,
    GroomingValue,
    HousingValue,
    NoiseValue,
    SizeValue,
    SpeciesValue,
    get_required_pet_fields,
)

PetStatusValue = Literal["available", "pending", "adopted", "hidden", "draft"]
SheddingValue = Literal["low", "moderate", "high"]
MIN_BIO_LENGTH_FOR_LISTING = 20


class Pet(BaseModel):
    id: str = Field(alias="_id", description="Unique identifier for the pet, e.g. pet_dog_042")
    shelter_id: Optional[str] = Field(None, description="Owning shelter ID")
    status: PetStatusValue = Field(default="available", description="Listing status: available, pending, adopted, hidden, draft")
    listed_at: Optional[datetime] = Field(None, description="Timestamp when pet was first listed")
    updated_at: Optional[datetime] = Field(None, description="Timestamp of last update")
    name: str = Field(..., description="Pet name")
    species: str = Field(..., description="Species: dog, cat")
    breed: str = Field(..., description="Breed name")
    age_months: int = Field(..., ge=0, description="Age in months")
    gender: str = Field(..., description="Gender: Male, Female")
    size: str = Field(..., description="Size: small, medium, large")
    age_group: Optional[str] = Field(
        None,
        description="Life stage: puppy_or_kitten (<12 mo), young (12-35 mo), adult (36-83 mo), senior (84+ mo)",
    )
    weight_lbs: Optional[int] = Field(None, ge=1, description="Approximate weight in pounds")
    energy_level: int = Field(..., ge=1, le=5, description="Energy level rating from 1 to 5")
    grooming_needs: Optional[str] = Field(
        None,
        description="Grooming frequency: low, moderate, high",
    )
    shedding_level: Optional[str] = Field(
        None,
        description="Shedding level: low, moderate, high",
    )
    noise_level: Optional[str] = Field(
        None,
        description="Vocalization / noise level: quiet, moderate, vocal",
    )
    alone_time_tolerance: Optional[str] = Field(
        None,
        description="Tolerance for being left alone: low (<=3h), moderate (4-5h), high (6+h)",
    )
    experience_level_required: Optional[str] = Field(
        None,
        description="Adopter experience needed: first_time_friendly, experienced_preferred",
    )
    training_level: Optional[str] = Field(
        None,
        description="Training status: basic, house_trained, well_trained",
    )
    coat_type: Optional[str] = Field(
        None,
        description="Coat type: short, medium, long, curly_hypoallergenic",
    )
    special_needs: Optional[bool] = Field(
        False,
        description="Whether the pet has special medical or dietary needs",
    )
    good_with_kids: bool = Field(..., description="Whether pet is suitable for households with children")
    good_with_other_pets: bool = Field(..., description="Whether pet gets along with other companion animals")
    temperament: List[str] = Field(default_factory=list, description="Temperament tags, e.g. Active, Family Friendly")
    housing_requirement: str = Field(..., description="apartment, house_with_yard, house_without_yard, apartment_or_house")
    bio_text: str = Field(..., description="Narrative qualitative bio describing personality and habits")
    quirks: Optional[List[str]] = Field(default_factory=list, description="Unique quirks or behaviors")
    exercise_needs: Optional[str] = Field(None, description="Exercise and activity requirements")
    triggers: Optional[List[str]] = Field(default_factory=list, description="Known sensitivities or behavioral triggers")
    hypoallergenic: bool = Field(default=False, description="Whether the pet is hypoallergenic (low allergen)")
    photo_url: Optional[str] = Field(None, description="Image URL or asset identifier for UI rendering")
    embedding: Optional[List[float]] = Field(default=None, description="768-dimensional float embedding vector")
    embedding_pending: bool = Field(default=False, description="True if embedding generation failed and needs retry")

    # Optional health & fee metadata
    vaccinated: Optional[bool] = Field(None, description="Whether vaccinations are up to date")
    neutered: Optional[bool] = Field(None, description="Whether pet is spayed/neutered")
    microchipped: Optional[bool] = Field(None, description="Whether pet is microchipped")
    adoption_fee: Optional[float] = Field(None, ge=0, description="Adoption fee in local currency")

    # Optional ideal-adopter requirements
    requires_yard: Optional[bool] = Field(None, description="Explicit yard requirement flag")
    min_experience: Optional[str] = Field(None, description="Minimum adopter experience note")
    not_suitable_for_young_children: Optional[bool] = Field(None, description="True if unsuitable for young children")
    ideal_adopter_notes: Optional[str] = Field(None, max_length=1000, description="Free-text ideal adopter notes")

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "_id": "pet_dog_042",
                "name": "Buddy",
                "species": "dog",
                "breed": "Golden Retriever",
                "age_months": 24,
                "gender": "Male",
                "size": "medium",
                "energy_level": 4,
                "good_with_kids": True,
                "good_with_other_pets": True,
                "temperament": ["Active", "Family Friendly", "Good with Kids"],
                "housing_requirement": "apartment_or_house",
                "bio_text": "A playful and affectionate boy who loves walks, belly rubs, and being around people!",
                "quirks": ["Carries a favorite tennis ball everywhere", "Greets you with happy tippy-taps"],
                "exercise_needs": "60+ minutes daily walks and fetch sessions",
                "triggers": ["Loud thunder storms", "Sudden loud vacuums"],
                "photo_url": "https://images.unsplash.com/photo-1552053831-71594a27632d",
                "embedding": [0.0124, -0.0431, 0.0892]
            }
        }
    }


class PetResponse(Pet):
    """Pet API representation without internal vector-search data."""

    embedding: Optional[List[float]] = Field(default=None, exclude=True)
    shelter_name: Optional[str] = Field(default=None, description="Display name of the listing shelter")
    shelter_city: Optional[str] = Field(default=None, description="City of the listing shelter")

    # Match-quality disclosure. Set by retrieval when a soft preference had to be
    # dropped to include this pet, so clients can label it a near match.
    is_relaxed_match: bool = Field(
        default=False,
        description="True when this pet was returned by relaxing one or more adopter preferences",
    )
    relaxed_fields: List[str] = Field(
        default_factory=list,
        description="Adopter constraint names that were relaxed to include this pet",
    )


def validate_complete_for_available(pet_data: Dict[str, Any]) -> None:
    """
    Validate that every matchable field from matching_schema is populated and
    bio_text meets the minimum length before a pet can be set to status='available'.
    Raises ValueError with clear field details if incomplete.
    """
    required = get_required_pet_fields() - {"age_group"}  # age_group is computed server-side from age_months
    missing = [f for f in sorted(required) if pet_data.get(f) is None]
    if missing:
        raise ValueError(
            f"All matchable fields are required before listing as available. Missing: {', '.join(missing)}"
        )
    bio = (pet_data.get("bio_text") or "").strip()
    if len(bio) < MIN_BIO_LENGTH_FOR_LISTING:
        raise ValueError(
            f"bio_text must be at least {MIN_BIO_LENGTH_FOR_LISTING} characters for semantic matching."
        )


class PetCreateRequest(BaseModel):
    """
    Request payload for shelter pet creation.
    Drafts (status='draft') may omit optional matchable fields;
    available listings (status='available') must satisfy every field in matching_schema.
    """
    name: str = Field(..., min_length=1, max_length=80)
    species: SpeciesValue
    breed: str = Field(..., min_length=1, max_length=80)
    age_months: int = Field(..., ge=0, le=360)
    gender: Literal["Male", "Female"]
    size: SizeValue
    weight_lbs: Optional[int] = Field(None, ge=1, le=300)
    energy_level: int = Field(..., ge=1, le=5)
    grooming_needs: Optional[GroomingValue] = None
    shedding_level: Optional[SheddingValue] = None
    noise_level: Optional[NoiseValue] = None
    alone_time_tolerance: Optional[AloneToleranceValue] = None
    experience_level_required: Optional[ExperienceValue] = None
    training_level: Optional[str] = None
    coat_type: Optional[str] = None
    special_needs: bool = False
    good_with_kids: bool
    good_with_other_pets: bool
    temperament: List[str] = Field(default_factory=list)
    housing_requirement: HousingValue
    bio_text: str = Field(default="")
    quirks: List[str] = Field(default_factory=list)
    exercise_needs: Optional[str] = None
    triggers: List[str] = Field(default_factory=list)
    hypoallergenic: bool = False
    photo_url: Optional[str] = None
    status: Literal["available", "draft"] = "available"

    # Optional health & fee metadata
    vaccinated: Optional[bool] = None
    neutered: Optional[bool] = None
    microchipped: Optional[bool] = None
    adoption_fee: Optional[float] = Field(None, ge=0)

    # Optional ideal-adopter requirements
    requires_yard: Optional[bool] = None
    min_experience: Optional[str] = None
    not_suitable_for_young_children: Optional[bool] = None
    ideal_adopter_notes: Optional[str] = Field(None, max_length=1000)

    # Optional client-generated key so a retried request creates one pet, not two.
    client_request_id: Optional[str] = Field(None, max_length=64)

    @model_validator(mode="after")
    def _validate_listing_completeness(self) -> "PetCreateRequest":
        if self.status == "available":
            validate_complete_for_available(self.model_dump())
        return self


class PetUpdateRequest(BaseModel):
    """Partial update payload for a shelter's pet."""
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    species: Optional[SpeciesValue] = None
    breed: Optional[str] = Field(None, min_length=1, max_length=80)
    age_months: Optional[int] = Field(None, ge=0, le=360)
    gender: Optional[Literal["Male", "Female"]] = None
    size: Optional[SizeValue] = None
    weight_lbs: Optional[int] = Field(None, ge=1, le=300)
    energy_level: Optional[int] = Field(None, ge=1, le=5)
    grooming_needs: Optional[GroomingValue] = None
    shedding_level: Optional[SheddingValue] = None
    noise_level: Optional[NoiseValue] = None
    alone_time_tolerance: Optional[AloneToleranceValue] = None
    experience_level_required: Optional[ExperienceValue] = None
    training_level: Optional[str] = None
    coat_type: Optional[str] = None
    special_needs: Optional[bool] = None
    good_with_kids: Optional[bool] = None
    good_with_other_pets: Optional[bool] = None
    temperament: Optional[List[str]] = None
    housing_requirement: Optional[HousingValue] = None
    bio_text: Optional[str] = None
    quirks: Optional[List[str]] = None
    exercise_needs: Optional[str] = None
    triggers: Optional[List[str]] = None
    hypoallergenic: Optional[bool] = None
    photo_url: Optional[str] = None
    status: Optional[PetStatusValue] = None

    vaccinated: Optional[bool] = None
    neutered: Optional[bool] = None
    microchipped: Optional[bool] = None
    adoption_fee: Optional[float] = Field(None, ge=0)

    requires_yard: Optional[bool] = None
    min_experience: Optional[str] = None
    not_suitable_for_young_children: Optional[bool] = None
    ideal_adopter_notes: Optional[str] = Field(None, max_length=1000)


class PetStatusUpdateRequest(BaseModel):
    """Request payload for PATCH /shelters/me/pets/{id}/status."""
    status: PetStatusValue
