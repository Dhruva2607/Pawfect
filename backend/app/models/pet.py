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
    energy_level: int = Field(..., ge=1, le=5, description="Energy level rating from 1 to 5")
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

