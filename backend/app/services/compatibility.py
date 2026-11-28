"""
Shared compatibility scoring helper used by both:
- POST /matches/direct-eval
- POST /adoptions/apply (computes applicant compatibility score for the shelter)

Reuses the grounded LLM evaluation with a deterministic heuristic fallback.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Tuple

from app.models.pet import Pet
from app.services.llm import get_chat_llm
from app.services.nodes import SinglePetCompatibility

logger = logging.getLogger(__name__)


def compute_heuristic_compatibility(
    pet: Pet,
    lifestyle: Dict[str, Any],
) -> SinglePetCompatibility:
    """Deterministic compatibility scorer used when LLM is unavailable or skipped."""
    score = 78
    pros: List[str] = []
    caveats: List[str] = []

    housing = (lifestyle.get("housing_type") or "").lower().replace(" ", "_")
    if housing in ("apartment", "house_without_yard") and pet.housing_requirement == "house_with_yard":
        score -= 24
        caveats.append("Requires a house with a yard")
    elif housing and housing == pet.housing_requirement:
        score += 6
        pros.append(f"Ideal housing match ({pet.housing_requirement.replace('_', ' ')})")
    else:
        score += 3
        pros.append(f"Matches housing requirement ({pet.housing_requirement.replace('_', ' ')})")

    if lifestyle.get("has_children") is True:
        if not pet.good_with_kids:
            score -= 28
            caveats.append("Not recommended for households with young children")
        else:
            score += 4
            pros.append("Good with children")

    if lifestyle.get("has_other_pets") is True:
        if not pet.good_with_other_pets:
            score -= 22
            caveats.append("Prefers to be the only pet")
        else:
            score += 4
            pros.append("Gets along with other pets")

    energy_budget = lifestyle.get("energy_budget")
    if isinstance(energy_budget, int):
        diff = abs(pet.energy_level - energy_budget)
        if diff == 0:
            score += 7
            pros.append(f"Energy level ({pet.energy_level}/5) is an exact match for your routine")
        elif diff == 1:
            score += 2
            pros.append(f"Energy level ({pet.energy_level}/5) aligns closely with your routine")
        else:
            score -= min(20, diff * 7)
            caveats.append(f"Energy level ({pet.energy_level}/5) differs from your {energy_budget}/5 budget")

    if housing in ("apartment", "house_without_yard"):
        if pet.noise_level == "quiet":
            score += 4
            pros.append("Quiet indoors — great for apartment neighbors")
        elif pet.noise_level == "vocal":
            score -= 8
            caveats.append("Vocal personality may need extra consideration in apartments")

    exp = (lifestyle.get("experience_level") or "").lower()
    if exp == "first_time" and pet.experience_level_required == "experienced_preferred":
        score -= 12
        caveats.append("Best suited for an experienced pet owner")
    elif exp == "experienced" and pet.experience_level_required == "experienced_preferred":
        score += 4
        pros.append("Your experience fits their training needs")
    elif pet.experience_level_required == "first_time_friendly":
        score += 3

    alone_hours = lifestyle.get("daily_alone_hours")
    if isinstance(alone_hours, int):
        if alone_hours >= 6 and pet.alone_time_tolerance == "low":
            score -= 14
            caveats.append("Needs frequent company and dislikes long hours alone")
        elif alone_hours >= 6 and pet.alone_time_tolerance == "high":
            score += 4
            pros.append("Comfortable spending longer stretches alone")

    if lifestyle.get("allergies") is True:
        if pet.hypoallergenic or pet.shedding_level == "low":
            score += 4
            pros.append("Low-shedding / allergy-friendly coat")
        else:
            score -= 22
            caveats.append("Moderate/high shedding may trigger allergies")

    pref_size = (lifestyle.get("preferred_size") or "").lower()
    if pref_size in ("small", "medium", "large"):
        if pet.size == pref_size:
            score += 3
        else:
            score -= 5
            caveats.append(f"Size is {pet.size} (you noted {pref_size})")

    pref_age = (lifestyle.get("preferred_age_group") or "").lower()
    if pref_age in ("puppy_or_kitten", "young", "adult", "senior") and pet.age_group:
        if pet.age_group == pref_age:
            score += 3
        else:
            score -= 4

    if not caveats:
        caveats.append(f"Exercise requirement: {pet.exercise_needs or 'Moderate daily activity'}")

    score = max(30, min(98, score))
    return SinglePetCompatibility(
        pet_id=pet.id,
        pet_name=pet.name,
        compatibility_score=score,
        pros=pros[:3] or [f"Suitable {pet.species} companion"],
        caveats=caveats[:2],
        reasoning_summary=f"{pet.name} ({pet.breed}) scored {score}% compatibility based on housing, household, and energy alignment.",
    )


async def evaluate_pet_compatibility(
    pet: Pet,
    lifestyle: Dict[str, Any],
    *,
    use_llm: bool = True,
) -> SinglePetCompatibility:
    """
    Compute compatibility score + pros/caveats/reasoning for a pet and adopter lifestyle.
    Falls back to deterministic heuristic scoring if LLM fails or is disabled.
    """
    if not use_llm:
        return compute_heuristic_compatibility(pet, lifestyle)

    dossier = {
        "id": pet.id,
        "name": pet.name,
        "species": pet.species,
        "breed": pet.breed,
        "age_months": pet.age_months,
        "age_group": pet.age_group,
        "size": pet.size,
        "weight_lbs": pet.weight_lbs,
        "energy_level": pet.energy_level,
        "grooming_needs": pet.grooming_needs,
        "shedding_level": pet.shedding_level,
        "noise_level": pet.noise_level,
        "alone_time_tolerance": pet.alone_time_tolerance,
        "experience_level_required": pet.experience_level_required,
        "training_level": pet.training_level,
        "coat_type": pet.coat_type,
        "special_needs": pet.special_needs,
        "housing_requirement": pet.housing_requirement,
        "good_with_kids": pet.good_with_kids,
        "good_with_other_pets": pet.good_with_other_pets,
        "hypoallergenic": pet.hypoallergenic,
        "temperament": pet.temperament,
        "exercise_needs": pet.exercise_needs,
        "quirks": pet.quirks,
        "triggers": pet.triggers,
        "bio_text": pet.bio_text,
    }

    system_prompt = (
        "You are the Lead Adoption Counselor and Compatibility Engine for PawFect.\n"
        "Analyze the provided pet and adopter lifestyle to compute an explainable, grounded compatibility evaluation.\n\n"
        "GUARDRAILS [FROM STEP 6.1]:\n"
        "- Base all reasoning strictly on the pet's documented traits. Never hallucinate.\n"
        "- Score: 0-100%.\n"
        "- Pros: 2-3 specific lifestyle alignment statements.\n"
        "- Caveats: 1-2 realistic watch-outs or considerations.\n"
    )
    human_prompt = (
        f"Adopter Lifestyle: {json.dumps(lifestyle, indent=2)}\n\n"
        f"Target Pet Dossier: {json.dumps(dossier, indent=2)}\n\n"
        "Generate a structured compatibility evaluation."
    )

    try:
        llm = await asyncio.to_thread(get_chat_llm, temperature=0.1)
        structured_llm = llm.with_structured_output(SinglePetCompatibility)
        return await structured_llm.ainvoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": human_prompt},
        ])
    except Exception as e:
        logger.warning("Compatibility LLM error: %s. Using heuristic fallback.", e)
        return compute_heuristic_compatibility(pet, lifestyle)
