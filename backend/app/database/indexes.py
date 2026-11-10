"""
MongoDB index configuration and Atlas Vector Search index definition.
[FROM MARKDOWN] matches Step 1.1 and Step 1.2.
"""

import logging
from typing import Any, Dict
from pymongo.database import Database
from pymongo import ASCENDING
from pymongo.errors import PyMongoError
from app.database.connection import get_sync_db

logger = logging.getLogger(__name__)

# [FROM MARKDOWN: Step 1.2] Atlas Vector Search index definition:
# Cosine similarity on the `embedding` field of the `pets` collection calibrated to 768 dimensions.
ATLAS_VECTOR_SEARCH_INDEX_NAME = "vector_index"

ATLAS_VECTOR_SEARCH_INDEX_DEFINITION: Dict[str, Any] = {
    "name": ATLAS_VECTOR_SEARCH_INDEX_NAME,
    "type": "vectorSearch",
    "definition": {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": 768,
                "similarity": "cosine"
            },
            {
                "type": "filter",
                "path": "species"
            },
            {
                "type": "filter",
                "path": "good_with_other_pets"
            },
            {
                "type": "filter",
                "path": "good_with_kids"
            },
            {
                "type": "filter",
                "path": "housing_requirement"
            },
            {
                "type": "filter",
                "path": "energy_level"
            }
        ]
    }
}


def setup_standard_indexes(db: Database | None = None) -> Dict[str, list]:
    """
    Creates standard indexes on MongoDB collections [FROM MARKDOWN: Step 1.1]:
    - pets: species, energy_level, good_with_kids
    - adoption_applications: user_id, pet_id, stage_status
    - user_profiles: email (unique)
    - match_evaluations: session_id, pet_id
    - user_sessions: updated_at
    """
    if db is None:
        db = get_sync_db()

    created_indexes: Dict[str, list] = {}

    # Pets collection indexes [FROM MARKDOWN: species, energy_level, good_with_kids]
    pets_col = db["pets"]
    idx_species = pets_col.create_index([("species", ASCENDING)], name="idx_species")
    idx_energy = pets_col.create_index([("energy_level", ASCENDING)], name="idx_energy_level")
    idx_kids = pets_col.create_index([("good_with_kids", ASCENDING)], name="idx_good_with_kids")
    idx_compound = pets_col.create_index(
        [("species", ASCENDING), ("energy_level", ASCENDING), ("good_with_kids", ASCENDING)],
        name="idx_species_energy_kids"
    )
    created_indexes["pets"] = [idx_species, idx_energy, idx_kids, idx_compound]

    # Adoption applications indexes
    adoptions_col = db["adoption_applications"]
    idx_user = adoptions_col.create_index([("user_id", ASCENDING)], name="idx_app_user_id")
    idx_pet = adoptions_col.create_index([("pet_id", ASCENDING)], name="idx_app_pet_id")
    idx_stage = adoptions_col.create_index([("stage_status", ASCENDING)], name="idx_app_stage")
    created_indexes["adoption_applications"] = [idx_user, idx_pet, idx_stage]

    # User profiles indexes
    profiles_col = db["user_profiles"]
    idx_email = profiles_col.create_index([("email", ASCENDING)], unique=True, name="idx_profile_email")
    created_indexes["user_profiles"] = [idx_email]

    # Match evaluations indexes
    evals_col = db["match_evaluations"]
    idx_eval_session = evals_col.create_index([("session_id", ASCENDING)], name="idx_eval_session")
    idx_eval_pet = evals_col.create_index([("pet_id", ASCENDING)], name="idx_eval_pet")
    idx_eval_session_pet = evals_col.create_index(
        [("session_id", ASCENDING), ("pet_id", ASCENDING)],
        name="idx_eval_session_pet"
    )
    created_indexes["match_evaluations"] = [idx_eval_session, idx_eval_pet, idx_eval_session_pet]

    # User sessions indexes
    sessions_col = db["user_sessions"]
    idx_session_upd = sessions_col.create_index([("updated_at", ASCENDING)], name="idx_session_updated")
    created_indexes["user_sessions"] = [idx_session_upd]

    return created_indexes


def setup_atlas_vector_search_index(db: Database | None = None) -> bool:
    """
    Attempts to create or verify the Atlas Vector Search index via PyMongo Search Index APIs.
    If the MongoDB deployment does not support programmatic search index creation (e.g. shared tier or non-Atlas),
    it logs the exact JSON definition for the Atlas UI.
    """
    if db is None:
        db = get_sync_db()

    pets_col = db["pets"]

    try:
        # Check if search index API is available (PyMongo >= 4.5 and MongoDB Atlas cluster)
        existing_indexes = list(pets_col.list_search_indexes())
        for idx in existing_indexes:
            if idx.get("name") == ATLAS_VECTOR_SEARCH_INDEX_NAME:
                existing_definition = idx.get("latestDefinition", idx.get("definition"))
                desired_definition = ATLAS_VECTOR_SEARCH_INDEX_DEFINITION["definition"]
                if existing_definition == desired_definition:
                    logger.info("Atlas Vector Search index '%s' already exists.", ATLAS_VECTOR_SEARCH_INDEX_NAME)
                    return True

                pets_col.update_search_index(
                    ATLAS_VECTOR_SEARCH_INDEX_NAME,
                    desired_definition
                )
                logger.info("Atlas Vector Search index '%s' updated.", ATLAS_VECTOR_SEARCH_INDEX_NAME)
                return True

        from pymongo.operations import SearchIndexModel
        model = SearchIndexModel(
            definition=ATLAS_VECTOR_SEARCH_INDEX_DEFINITION["definition"],
            name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
            type=ATLAS_VECTOR_SEARCH_INDEX_DEFINITION["type"]
        )
        pets_col.create_search_index(model=model)
        logger.info("Atlas Vector Search index '%s' created successfully.", ATLAS_VECTOR_SEARCH_INDEX_NAME)
        return True
    except (PyMongoError, AttributeError) as e:
        logger.warning(
            "Programmatic Atlas Vector Search index creation not supported or requires Atlas UI/API: %s. "
            "Index definition is preserved in ATLAS_VECTOR_SEARCH_INDEX_DEFINITION.",
            e
        )
        return False
