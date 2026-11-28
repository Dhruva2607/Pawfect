"""
Pet embedding text builder and async embedding generator.
Uses the exact same text template as `seed_pets.py` so shelter-listed pets
live in the exact same semantic vector space as seeded pets.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from app.services.embedding import generate_embedding

logger = logging.getLogger(__name__)

EMBEDDING_RELEVANT_FIELDS = {
    "bio_text",
    "breed",
    "temperament",
    "quirks",
    "traits",
    "species",
    "age_months",
    "size",
    "energy_level",
    "grooming_needs",
    "shedding_level",
    "noise_level",
    "alone_time_tolerance",
    "experience_level_required",
    "housing_requirement",
    "good_with_kids",
    "good_with_other_pets",
    "exercise_needs",
    "triggers",
    "hypoallergenic",
}


def create_pet_embedding_text(pet: Dict[str, Any]) -> str:
    """
    Constructs a rich narrative document representation for semantic vector search.
    Matches the template in `app/scripts/seed_pets.py`.
    """
    temperament_str = ", ".join(pet.get("temperament") or [])
    quirks_str = "; ".join(pet.get("quirks") or [])
    triggers_str = "; ".join(pet.get("triggers") or [])

    return (
        f"Species: {pet.get('species')}. "
        f"Breed: {pet.get('breed')}. "
        f"Age: {pet.get('age_months')} months ({pet.get('age_group', 'adult')}). Gender: {pet.get('gender')}. "
        f"Size: {pet.get('size')} ({pet.get('weight_lbs', 'N/A')} lbs). Energy Level: {pet.get('energy_level')}/5. "
        f"Grooming needs: {pet.get('grooming_needs', 'moderate')}. Shedding: {pet.get('shedding_level', 'moderate')}. "
        f"Coat: {pet.get('coat_type', 'short')}. Noise level: {pet.get('noise_level', 'moderate')}. "
        f"Alone time tolerance: {pet.get('alone_time_tolerance', 'moderate')}. "
        f"Experience level: {pet.get('experience_level_required', 'first_time_friendly')}. "
        f"Training: {pet.get('training_level', 'basic')}. "
        f"Housing: {pet.get('housing_requirement')}. "
        f"Good with kids: {pet.get('good_with_kids')}. Good with other pets: {pet.get('good_with_other_pets')}. "
        f"Temperament: {temperament_str}. "
        f"Bio: {pet.get('bio_text')} "
        f"Quirks: {quirks_str}. "
        f"Exercise needs: {pet.get('exercise_needs')}. "
        f"Triggers: {triggers_str}."
    )


async def generate_pet_embedding_async(pet_doc: Dict[str, Any]) -> Tuple[Optional[List[float]], bool]:
    """
    Generate a 768-dim embedding off the event loop via asyncio.to_thread.
    Returns (embedding_vector, embedding_pending).
    If generation fails, returns (None, True) so the caller can mark
    embedding_pending=True / status='hidden' and offer a retry path.
    """
    text = create_pet_embedding_text(pet_doc)
    try:
        vector = await asyncio.to_thread(generate_embedding, text)
        if vector and len(vector) == 768:
            return vector, False
        logger.warning("Generated embedding had unexpected length (%s)", len(vector) if vector else 0)
        return None, True
    except Exception as e:
        logger.warning("Pet embedding generation failed for %s: %s", pet_doc.get("_id"), e)
        return None, True
