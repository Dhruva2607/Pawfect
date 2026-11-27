"""
Pydantic v2 schema for Pet documents.
[FROM MARKDOWN] matches Step 1.1, Step 1.3 and sample JSON in Section 5.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Pet(BaseModel):
    id: str = Field(alias="_id", description="Unique identifier for the pet, e.g. pet_dog_042")
    name: str = Field(..., description="Pet name")
    species: str = Field(..., description="Species: dog, cat, etc.")
    breed: str = Field(..., description="Breed name")
    age_months: int = Field(..., description="Age in months")
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
        description="Tolerance for being left alone: low (<=3h), moderate (4-6h), high (6-8h+)",
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
    housing_requirement: str = Field(..., description="apartment, house_with_yard, apartment_or_house")
    bio_text: str = Field(..., description="Narrative qualitative bio describing personality and habits")
    quirks: Optional[List[str]] = Field(default_factory=list, description="Unique quirks or behaviors")
    exercise_needs: Optional[str] = Field(None, description="Exercise and activity requirements")
    triggers: Optional[List[str]] = Field(default_factory=list, description="Known sensitivities or behavioral triggers")
    photo_url: Optional[str] = Field(None, description="Image URL or asset identifier for UI rendering")
    embedding: Optional[List[float]] = Field(default=None, description="768-dimensional float embedding vector")

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
