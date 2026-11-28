"""
Idempotent migration script to backfill shelter ownership and new Pet fields
onto existing seeded pets.

What it does:
1. Creates the default "PawFect Partner Shelter" (`shelter_default_001`) if missing.
2. Assigns `shelter_id = "shelter_default_001"` to all pets missing `shelter_id`.
3. Sets `status = "available"` on pets missing `status`.
4. Backfills `hypoallergenic` (True if shedding_level == "low" or coat_type == "curly_hypoallergenic"
   or "hypoallergenic" in temperament/bio_text, else False) where missing.
5. Backfills `listed_at` and `updated_at` timestamps where missing.
6. Backfills `age_group` from `age_months` where missing.

Safe to re-run repeatedly: never wipes or duplicates data.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict

from pymongo.database import Database

from app.database.connection import get_sync_db
from app.services.auth import hash_password
from app.services.matching_schema import compute_age_group

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

DEFAULT_SHELTER_ID = "shelter_default_001"
DEFAULT_SHELTER_EMAIL = "partner@pawfect.local"


def _infer_hypoallergenic(pet: Dict[str, Any]) -> bool:
    if (pet.get("shedding_level") or "").lower() == "low":
        return True
    if (pet.get("coat_type") or "").lower() == "curly_hypoallergenic":
        return True
    temperament = " ".join(pet.get("temperament") or []).lower()
    bio = (pet.get("bio_text") or "").lower()
    return "hypoallergenic" in temperament or "hypoallergenic" in bio


def migrate_shelters(db: Database | None = None) -> Dict[str, int]:
    """Run idempotent shelter migration on the given (or default sync) database."""
    if db is None:
        db = get_sync_db()

    now = datetime.now(timezone.utc)
    shelters_col = db["shelters"]
    pets_col = db["pets"]

    # 1. Ensure default PawFect Partner Shelter exists
    existing_shelter = shelters_col.find_one({"_id": DEFAULT_SHELTER_ID})
    created_default = 0
    if not existing_shelter:
        shelters_col.insert_one({
            "_id": DEFAULT_SHELTER_ID,
            "name": "PawFect Partner Shelter",
            "email": DEFAULT_SHELTER_EMAIL,
            "password_hash": hash_password("PawFectPartner2026!"),
            "contact_phone": "+91-80-4000-1234",
            "address": "100 Indiranagar 12th Main",
            "city": "Bengaluru",
            "state": "Karnataka",
            "country": "India",
            "description": "Official PawFect partner adoption center caring for rescued dogs and cats.",
            "operating_hours": "Tue-Sun 10:00 AM - 6:00 PM",
            "verified": True,
            "created_at": now,
            "updated_at": now,
        })
        created_default = 1
        logger.info("Created default shelter '%s' (%s).", DEFAULT_SHELTER_ID, DEFAULT_SHELTER_EMAIL)
    else:
        logger.info("Default shelter '%s' already exists; skipping creation.", DEFAULT_SHELTER_ID)

    # 2. Backfill existing pets without wiping or duplicating
    updated_pets = 0
    for pet in pets_col.find({}):
        patch: Dict[str, Any] = {}
        if not pet.get("shelter_id"):
            patch["shelter_id"] = DEFAULT_SHELTER_ID
        if not pet.get("status"):
            patch["status"] = "available"
        if "hypoallergenic" not in pet or pet.get("hypoallergenic") is None:
            patch["hypoallergenic"] = _infer_hypoallergenic(pet)
        if not pet.get("age_group") and isinstance(pet.get("age_months"), int):
            patch["age_group"] = compute_age_group(pet["age_months"])
        if not pet.get("listed_at"):
            patch["listed_at"] = now
        if not pet.get("updated_at"):
            patch["updated_at"] = now
        if "embedding_pending" not in pet:
            patch["embedding_pending"] = not bool(pet.get("embedding") and len(pet["embedding"]) == 768)

        if patch:
            pets_col.update_one({"_id": pet["_id"]}, {"$set": patch})
            updated_pets += 1

    logger.info("Migration complete: created_default_shelter=%d, updated_pets=%d", created_default, updated_pets)
    return {"created_default_shelter": created_default, "updated_pets": updated_pets}


if __name__ == "__main__":
    migrate_shelters()
