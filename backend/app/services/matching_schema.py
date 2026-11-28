"""
Single Source of Truth for PawFect matching dimensions.

Every matchable dimension is defined ONCE here — allowed values, display labels,
the adopter field it pairs with, and the pet field it maps to.  This module is
imported by:
    • LifestyleConstraints (state.py)
    • the chatbot question flow and quick replies (nodes.py)
    • build_mql_prefilter (retrieval.py)
    • shelter pet validation (Pet Pydantic model)
    • GET /api/v1/meta/pet-options (meta.py router)
    • coverage test (tests/test_matching_schema.py)

Adding a new matchable dimension later requires ONLY an entry in
MATCHING_DIMENSIONS below; the chatbot will ask about it and the shelter form
will collect it automatically.

daily_alone_hours → alone_time_tolerance mapping
─────────────────────────────────────────────────
    0 – 3 hours  →  "low"       (pet can tolerate ≤ 3 h alone)
    4 – 5 hours  →  "moderate"  (pet can tolerate 4-6 h alone)
    6+   hours   →  "high"      (pet can tolerate 6-8+ h alone)

housing normalization
─────────────────────
    apartment            →  adopter lives in an apartment (no yard)
    house_with_yard      →  adopter has a house with outdoor space
    house_without_yard   →  adopter has a house but NO yard
                            (treated like apartment for housing filters —
                             NOT matched with pets that require a yard)
    apartment_or_house   →  adopter is flexible / pet works anywhere
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Sequence, Tuple


# ── Core value types ──────────────────────────────────────────────────

SpeciesValue = Literal["dog", "cat"]
SizeValue = Literal["small", "medium", "large"]
AgeGroupValue = Literal["puppy_or_kitten", "young", "adult", "senior"]
GroomingValue = Literal["low", "moderate", "high"]
NoiseValue = Literal["quiet", "moderate", "vocal"]
AloneToleranceValue = Literal["low", "moderate", "high"]
ExperienceValue = Literal["first_time_friendly", "experienced_preferred"]
HousingValue = Literal["apartment", "house_with_yard", "house_without_yard", "apartment_or_house"]


# ── Dimension definition ─────────────────────────────────────────────

@dataclass(frozen=True)
class MatchingDimension:
    """One matchable dimension pairing an adopter field to a pet field."""
    adopter_field: str
    pet_field: str                             # field name on the Pet document
    allowed_pet_values: Sequence[str]          # canonical allowed values for the pet field
    display_labels: Dict[str, str]             # value → human-readable label
    chat_question: str                         # question the chatbot asks the adopter
    chat_quick_replies: List[str]              # quick-reply chips for mobile UI
    is_boolean: bool = False                   # True for yes/no dimensions
    is_numeric: bool = False                   # True for integer-range dimensions (e.g. energy)
    pet_field_required: bool = True            # required before a pet is "available"


# ── All matchable dimensions ─────────────────────────────────────────

MATCHING_DIMENSIONS: Dict[str, MatchingDimension] = {
    "species": MatchingDimension(
        adopter_field="species",
        pet_field="species",
        allowed_pet_values=["dog", "cat"],
        display_labels={"dog": "Dog", "cat": "Cat"},
        chat_question="Are you looking to adopt a dog or a cat?",
        chat_quick_replies=["Looking for a Dog", "Looking for a Cat", "Open to either"],
    ),
    "size": MatchingDimension(
        adopter_field="preferred_size",
        pet_field="size",
        allowed_pet_values=["small", "medium", "large"],
        display_labels={"small": "Small", "medium": "Medium", "large": "Large"},
        chat_question="What size pet would suit your home best?",
        chat_quick_replies=["Small", "Medium", "Large", "Any size"],
    ),
    "age_group": MatchingDimension(
        adopter_field="preferred_age_group",
        pet_field="age_group",
        allowed_pet_values=["puppy_or_kitten", "young", "adult", "senior"],
        display_labels={
            "puppy_or_kitten": "Puppy or Kitten",
            "young": "Young (1-3 yrs)",
            "adult": "Adult (3-7 yrs)",
            "senior": "Senior (7+ yrs)",
        },
        chat_question="What age group are you hoping to adopt?",
        chat_quick_replies=["Puppy or Kitten", "Young (1-3 yrs)", "Adult (3-7 yrs)", "Senior (7+ yrs)", "Any age"],
    ),
    "grooming": MatchingDimension(
        adopter_field="grooming_tolerance",
        pet_field="grooming_needs",
        allowed_pet_values=["low", "moderate", "high"],
        display_labels={"low": "Low maintenance", "moderate": "Moderate brushing", "high": "High grooming"},
        chat_question="How much coat grooming and brushing are you comfortable with?",
        chat_quick_replies=["Low maintenance", "Moderate brushing", "High grooming is fine"],
    ),
    "noise": MatchingDimension(
        adopter_field="noise_tolerance",
        pet_field="noise_level",
        allowed_pet_values=["quiet", "moderate", "vocal"],
        display_labels={"quiet": "Quiet", "moderate": "Moderate", "vocal": "Vocal"},
        chat_question="What noise level works best for your household and neighbors?",
        chat_quick_replies=["Quiet (minimal barking/meowing)", "Moderate", "Vocal pets are fine"],
    ),
    "alone_time": MatchingDimension(
        adopter_field="daily_alone_hours",
        pet_field="alone_time_tolerance",
        allowed_pet_values=["low", "moderate", "high"],
        display_labels={"low": "Low (≤3 h)", "moderate": "Moderate (4-5 h)", "high": "High (6+ h)"},
        chat_question="Roughly how many hours a day would your pet spend alone?",
        chat_quick_replies=["0-3 hours", "4-6 hours", "6+ hours"],
        is_numeric=True,
    ),
    "experience": MatchingDimension(
        adopter_field="experience_level",
        pet_field="experience_level_required",
        allowed_pet_values=["first_time_friendly", "experienced_preferred"],
        display_labels={
            "first_time_friendly": "First-time friendly",
            "experienced_preferred": "Experienced preferred",
        },
        chat_question="Have you owned a pet before?",
        chat_quick_replies=["First-time owner", "Experienced owner"],
    ),
    "housing": MatchingDimension(
        adopter_field="housing_type",
        pet_field="housing_requirement",
        allowed_pet_values=["apartment", "house_with_yard", "house_without_yard", "apartment_or_house"],
        display_labels={
            "apartment": "Apartment",
            "house_with_yard": "House with yard",
            "house_without_yard": "House without yard",
            "apartment_or_house": "Apartment or House",
        },
        chat_question="What kind of living space do you have?",
        chat_quick_replies=["Apartment", "House with yard", "House without yard"],
    ),
    "children": MatchingDimension(
        adopter_field="has_children",
        pet_field="good_with_kids",
        allowed_pet_values=["true", "false"],
        display_labels={"true": "Yes", "false": "No"},
        chat_question="Do you have any children at home?",
        chat_quick_replies=["No children", "Have young children"],
        is_boolean=True,
    ),
    "other_pets": MatchingDimension(
        adopter_field="has_other_pets",
        pet_field="good_with_other_pets",
        allowed_pet_values=["true", "false"],
        display_labels={"true": "Yes", "false": "No"},
        chat_question="Do you have any other pets at home?",
        chat_quick_replies=["No other pets", "Have other pets"],
        is_boolean=True,
    ),
    "energy": MatchingDimension(
        adopter_field="energy_budget",
        pet_field="energy_level",
        allowed_pet_values=["1", "2", "3", "4", "5"],
        display_labels={"1": "Very calm", "2": "Calm", "3": "Moderate", "4": "Active", "5": "Very active"},
        chat_question="What activity level fits your daily routine best?",
        chat_quick_replies=["Calm & low energy", "Moderate daily walks", "High energy & active"],
        is_numeric=True,
    ),
    "allergies": MatchingDimension(
        adopter_field="allergies",
        pet_field="shedding_level",  # paired with shedding_level + hypoallergenic
        allowed_pet_values=["low", "moderate", "high"],
        display_labels={"low": "Low", "moderate": "Moderate", "high": "High"},
        chat_question="Do you or anyone in your home have pet allergies or need a low-shedding pet?",
        chat_quick_replies=["No allergies", "Yes, need low-shedding"],
        is_boolean=True,  # the adopter field is boolean
    ),
}


# ── Convenience accessors ────────────────────────────────────────────

def get_adopter_fields() -> set[str]:
    """Return all adopter-side field names used in the matching schema."""
    return {d.adopter_field for d in MATCHING_DIMENSIONS.values()}


def get_pet_fields() -> set[str]:
    """Return all pet-side field names used in the matching schema (excluding hypoallergenic)."""
    fields = {d.pet_field for d in MATCHING_DIMENSIONS.values()}
    fields.add("hypoallergenic")  # paired with allergies dimension
    return fields


def get_required_pet_fields() -> set[str]:
    """Return pet fields that must be filled before a pet is status='available'."""
    fields = {d.pet_field for d in MATCHING_DIMENSIONS.values() if d.pet_field_required}
    fields.add("hypoallergenic")
    return fields


def get_chat_question_flow() -> List[Tuple[str, str, List[str]]]:
    """
    Generate the ordered question flow for the chatbot intake.
    Returns list of (adopter_field, question, quick_replies).
    
    Order: species → age_group → size → grooming → noise → alone_time →
           experience → housing → energy → children/other_pets → allergies
    """
    # Explicit ordering to control conversation flow
    ordered_keys = [
        "species", "age_group", "size", "grooming", "noise",
        "alone_time", "experience", "housing", "energy",
        "children", "other_pets", "allergies",
    ]
    flow = []
    for key in ordered_keys:
        dim = MATCHING_DIMENSIONS[key]
        flow.append((dim.adopter_field, dim.chat_question, dim.chat_quick_replies))
    return flow


def get_pet_options_response() -> Dict:
    """
    Build the response payload for GET /api/v1/meta/pet-options.
    Android shelter form builds its dropdowns, chips, and sliders from this.
    """
    dimensions = {}
    for key, dim in MATCHING_DIMENSIONS.items():
        dimensions[key] = {
            "adopter_field": dim.adopter_field,
            "pet_field": dim.pet_field,
            "allowed_values": list(dim.allowed_pet_values),
            "display_labels": dict(dim.display_labels),
            "is_boolean": dim.is_boolean,
            "is_numeric": dim.is_numeric,
            "required_for_listing": dim.pet_field_required,
        }

    # Add hypoallergenic as a standalone boolean option
    dimensions["hypoallergenic"] = {
        "adopter_field": "allergies",
        "pet_field": "hypoallergenic",
        "allowed_values": ["true", "false"],
        "display_labels": {"true": "Yes", "false": "No"},
        "is_boolean": True,
        "is_numeric": False,
        "required_for_listing": True,
    }

    return {
        "dimensions": dimensions,
        "age_group_ranges": {
            "puppy_or_kitten": {"min_months": 0, "max_months": 11},
            "young": {"min_months": 12, "max_months": 35},
            "adult": {"min_months": 36, "max_months": 83},
            "senior": {"min_months": 84, "max_months": None},
        },
        "alone_hours_mapping": {
            "0-3": "low",
            "4-5": "moderate",
            "6+": "high",
        },
        "housing_normalization": {
            "apartment": "No yard. Matched with apartment or apartment_or_house pets.",
            "house_with_yard": "Has yard. Matched with apartment_or_house or house_with_yard pets.",
            "house_without_yard": "No yard despite being a house. Treated like apartment for housing filters. NOT matched with pets that require a yard.",
            "apartment_or_house": "Flexible housing. No housing filter applied.",
        },
    }


def compute_age_group(age_months: int) -> str:
    """Compute age_group from age_months. Used server-side; client value is ignored."""
    if age_months < 12:
        return "puppy_or_kitten"
    elif age_months < 36:
        return "young"
    elif age_months < 84:
        return "adult"
    else:
        return "senior"


def map_alone_hours_to_tolerance(hours: int) -> str:
    """
    Map daily_alone_hours integer to alone_time_tolerance value.
    
    0–3 hours  → "low"
    4–5 hours  → "moderate"
    6+ hours   → "high"
    """
    if hours >= 6:
        return "high"
    elif hours >= 4:
        return "moderate"
    else:
        return "low"


def get_intake_prompt_dimensions_block() -> str:
    """
    Generate the numbered dimension/value-list block for the chatbot's
    system_prompt directly from MATCHING_DIMENSIONS.
    """
    chat_keys = [
        "species",
        "age_group",
        "size",
        "grooming",
        "noise",
        "alone_time",
        "experience",
        "allergies",
    ]
    lines: List[str] = []
    for idx, key in enumerate(chat_keys, start=1):
        dim = MATCHING_DIMENSIONS[key]
        if dim.is_boolean and key == "allergies":
            val_desc = "boolean (low-shedding need)"
        elif dim.is_numeric and key == "alone_time":
            val_desc = "integer hours alone per day"
        else:
            quoted = ", ".join(f"'{v}'" for v in dim.allowed_pet_values)
            if key in ("species", "age_group", "size", "grooming", "noise"):
                quoted += ", or 'any'"
            val_desc = quoted
        lines.append(f"  {idx}. {dim.adopter_field}: {val_desc} -> {dim.chat_quick_replies}")
    return "\n".join(lines)
