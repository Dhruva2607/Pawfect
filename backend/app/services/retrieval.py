"""
Hybrid Retrieval Service: MQL Pre-filtering combined with Vector Similarity Search.
[FROM MARKDOWN] matches Step 2.3 and Section 3 (MongoDB Atlas Vector Search with hybrid pre-filtering).
"""

import math
import logging
from typing import List, Dict, Any, Optional
from pymongo.database import Database
from pymongo.errors import PyMongoError
from app.database.connection import get_sync_db
from app.services.embedding import generate_embedding
from app.database.indexes import ATLAS_VECTOR_SEARCH_INDEX_NAME

logger = logging.getLogger(__name__)


def compute_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for a, b in zip(vec_a, vec_b):
        dot += a * b
        norm_a += a * a
        norm_b += b * b

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


def build_mql_prefilter(constraints: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms extracted lifestyle constraints into MongoDB Query Language (MQL) pre-filters.
    [FROM MARKDOWN: Step 2.3 - Hard operational filters]
    """
    query: Dict[str, Any] = {}

    # Hard filter: only available pets are returned to adopters
    query["status"] = "available"

    # Species filter
    species = constraints.get("species")
    if species and species.lower() in ["dog", "cat"]:
        query["species"] = species.lower()

    # Children safety filter
    if constraints.get("has_children") is True:
        query["good_with_kids"] = True

    # Other pets compatibility filter
    if constraints.get("has_other_pets") is True:
        query["good_with_other_pets"] = True

    # Housing requirement filter — normalized per matching_schema.py
    # house_without_yard is treated like apartment (no yard access)
    housing = constraints.get("housing_type")
    if housing:
        housing_clean = housing.lower().replace(" ", "_")
        if "apartment_or_house" in housing_clean:
            # "Either is fine" — no housing restriction
            pass
        elif housing_clean == "house_without_yard":
            # House WITHOUT yard → same filter as apartment (no yard pets)
            query["housing_requirement"] = {"$in": ["apartment", "apartment_or_house"]}
        elif housing_clean == "house_with_yard":
            # House WITH yard → can take apartment_or_house or house_with_yard
            query["housing_requirement"] = {"$in": ["apartment_or_house", "house_with_yard"]}
        elif "apartment" in housing_clean:
            query["housing_requirement"] = {"$in": ["apartment", "apartment_or_house"]}

    # Energy compatibility: allow at most one level above the adopter's budget
    energy_budget = constraints.get("energy_budget")
    if isinstance(energy_budget, int):
        query["energy_level"] = {"$lte": min(5, energy_budget + 1)}

    # Size preference filter
    preferred_size = constraints.get("preferred_size")
    if preferred_size and preferred_size.lower() in ["small", "medium", "large"]:
        query["size"] = preferred_size.lower()

    # Age group preference filter
    preferred_age = constraints.get("preferred_age_group")
    if preferred_age and preferred_age.lower() in ["puppy_or_kitten", "young", "adult", "senior"]:
        query["age_group"] = preferred_age.lower()

    # Grooming tolerance filter
    grooming = constraints.get("grooming_tolerance")
    if grooming:
        grooming_clean = grooming.lower()
        if grooming_clean == "low":
            query["grooming_needs"] = "low"
        elif grooming_clean == "moderate":
            query["grooming_needs"] = {"$in": ["low", "moderate"]}

    # Noise tolerance filter
    noise = constraints.get("noise_tolerance")
    if noise:
        noise_clean = noise.lower()
        if noise_clean == "quiet":
            query["noise_level"] = "quiet"
        elif noise_clean == "moderate":
            query["noise_level"] = {"$in": ["quiet", "moderate"]}

    # Daily alone hours filter — mapped per matching_schema.py
    # 0-3 h → low, 4-5 h → moderate, 6+ h → high
    alone_hours = constraints.get("daily_alone_hours")
    if isinstance(alone_hours, int):
        if alone_hours >= 6:
            query["alone_time_tolerance"] = "high"
        elif alone_hours >= 4:
            query["alone_time_tolerance"] = {"$in": ["moderate", "high"]}

    # First-time owner experience filter
    experience = constraints.get("experience_level")
    if experience and experience.lower() == "first_time":
        query["experience_level_required"] = "first_time_friendly"

    # Hypoallergenic / allergy filter — no more regex on bio/temperament
    # Uses the structured hypoallergenic bool field + shedding_level == "low"
    if constraints.get("allergies") is True:
        query["$or"] = [
            {"shedding_level": "low"},
            {"hypoallergenic": True},
        ]

    return query


_SOFT_PREFERENCE_KEYS = (
    "preferred_size",
    "preferred_age_group",
    "grooming_tolerance",
    "noise_tolerance",
    "daily_alone_hours",
    "experience_level",
)


def _run_vector_or_cosine_search(
    pets_col: Any,
    query_vector: List[float],
    mql_filter: Dict[str, Any],
    top_k: int,
) -> List[Dict[str, Any]]:
    """Executes Atlas $vectorSearch with MQL filter, falling back to in-memory cosine ranking."""
    # Atlas Vector Search does not support the regex predicates used for allergy filtering.
    # Keep those searches on the regular MongoDB query path instead.
    if "$or" not in mql_filter:
        try:
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": ATLAS_VECTOR_SEARCH_INDEX_NAME,
                        "path": "embedding",
                        "queryVector": query_vector,
                        "numCandidates": top_k * 10,
                        "limit": top_k,
                        "filter": mql_filter if mql_filter else {}
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "name": 1,
                        "species": 1,
                        "breed": 1,
                        "age_months": 1,
                        "age_group": 1,
                        "gender": 1,
                        "size": 1,
                        "weight_lbs": 1,
                        "energy_level": 1,
                        "grooming_needs": 1,
                        "shedding_level": 1,
                        "noise_level": 1,
                        "alone_time_tolerance": 1,
                        "experience_level_required": 1,
                        "training_level": 1,
                        "coat_type": 1,
                        "special_needs": 1,
                        "good_with_kids": 1,
                        "good_with_other_pets": 1,
                        "temperament": 1,
                        "housing_requirement": 1,
                        "bio_text": 1,
                        "quirks": 1,
                        "exercise_needs": 1,
                        "triggers": 1,
                        "photo_url": 1,
                        "hypoallergenic": 1,
                        "status": 1,
                        "shelter_id": 1,
                        "listed_at": 1,
                        "adoption_fee": 1,
                        "vaccinated": 1,
                        "neutered": 1,
                        "microchipped": 1,
                        "requires_yard": 1,
                        "min_experience": 1,
                        "not_suitable_for_young_children": 1,
                        "ideal_adopter_notes": 1,
                        "score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]
            results = list(pets_col.aggregate(pipeline))
            if results:
                logger.info("Retrieved %d candidates via Atlas $vectorSearch.", len(results))
                return results
        except PyMongoError as e:
            logger.info(
                "Atlas $vectorSearch is unavailable; falling back to filtered cosine ranking: %s",
                e,
            )

    # Fallback: MQL pre-filter + in-memory cosine ranking
    candidates_cursor = pets_col.find(mql_filter)
    candidates = list(candidates_cursor)

    ranked: List[Dict[str, Any]] = []
    for pet in candidates:
        emb = pet.get("embedding")
        if emb and len(emb) == 768:
            score = compute_cosine_similarity(query_vector, emb)
        else:
            score = 0.0

        pet_clean = dict(pet)
        pet_clean.pop("embedding", None)
        pet_clean["score"] = round(score, 4)
        ranked.append(pet_clean)

    ranked.sort(key=lambda x: x["score"], reverse=True)
    top_candidates = ranked[:top_k]
    logger.info("Retrieved %d candidates via hybrid MQL + cosine ranking.", len(top_candidates))
    return top_candidates


def hybrid_search_pets(
    query_text: str,
    constraints: Dict[str, Any],
    top_k: int = 5,
    db: Optional[Database] = None
) -> List[Dict[str, Any]]:
    """
    Executes hybrid retrieval:
    1. Generates 768-dim embedding for semantic query.
    2. Applies MQL operational pre-filters.
    3. Scores matching pets by cosine similarity over embedding field.
    4. If fewer than top_k exact matches exist, fills remaining slots with near-match
       alternatives by relaxing soft preference filters (never dropping safety/species).
    """
    if db is None:
        db = get_sync_db()

    pets_col = db["pets"]
    query_vector = generate_embedding(query_text)

    # 1. Strict search with all constraints
    mql_filter = build_mql_prefilter(constraints)
    logger.info("Executing hybrid search with MQL filter: %s", mql_filter)
    results = _run_vector_or_cosine_search(pets_col, query_vector, mql_filter, top_k)

    # Track which adopter constraints were dropped to fill the candidate list, so
    # the scorer and UI can label these pets as near-matches rather than
    # presenting them as exact fits.
    relaxed: set[str] = set()

    # 2. If fewer than top_k matches and soft preferences were applied, relax soft preferences for alternatives
    if len(results) < top_k and any(constraints.get(k) is not None for k in _SOFT_PREFERENCE_KEYS):
        relaxed.update(k for k in _SOFT_PREFERENCE_KEYS if constraints.get(k) is not None)
        relaxed_constraints = {k: v for k, v in constraints.items() if k not in _SOFT_PREFERENCE_KEYS}
        relaxed_filter = build_mql_prefilter(relaxed_constraints)
        logger.info("Filling alternative matches with relaxed soft preferences: %s", relaxed_filter)
        extra = _run_vector_or_cosine_search(pets_col, query_vector, relaxed_filter, top_k * 2)
        seen_ids = {p.get("_id") for p in results}
        for pet in extra:
            if pet.get("_id") not in seen_ids:
                results.append(pet)
                seen_ids.add(pet.get("_id"))
                if len(results) >= top_k:
                    break

    # 3. If still fewer than top_k (e.g. strict energy/housing combo), relax energy/housing while keeping species/safety
    if len(results) < top_k and (constraints.get("energy_budget") is not None or constraints.get("housing_type") is not None):
        for dropped in ("energy_budget", "housing_type"):
            if constraints.get(dropped) is not None:
                relaxed.add(dropped)
        core_constraints = {
            k: v for k, v in constraints.items()
            if k in ("species", "has_children", "has_other_pets", "allergies")
        }
        core_filter = build_mql_prefilter(core_constraints)
        if core_filter != mql_filter:
            logger.info("Filling remaining alternative matches with core safety/species filter: %s", core_filter)
            extra = _run_vector_or_cosine_search(pets_col, query_vector, core_filter, top_k * 2)
            seen_ids = {p.get("_id") for p in results}
            for pet in extra:
                if pet.get("_id") not in seen_ids:
                    results.append(pet)
                    seen_ids.add(pet.get("_id"))
                    if len(results) >= top_k:
                        break

    finalized = _attach_shelter_metadata(results[:top_k], db)
    if relaxed:
        relaxed_list = sorted(relaxed)
        logger.info("Marking %d candidate(s) as near-match (relaxed: %s)", len(finalized), relaxed_list)
        for pet in finalized:
            pet["relaxed_fields"] = relaxed_list
            pet["is_relaxed_match"] = True
    else:
        for pet in finalized:
            pet["relaxed_fields"] = []
            pet["is_relaxed_match"] = False
    return finalized


def _attach_shelter_metadata(pets: List[Dict[str, Any]], db: Database) -> List[Dict[str, Any]]:
    """Enrich candidate pet dicts with shelter_name & shelter_city if shelters collection exists."""
    shelter_ids = list({p.get("shelter_id") for p in pets if p.get("shelter_id")})
    if not shelter_ids:
        return pets
    try:
        shelters_col = db["shelters"]
        docs = list(shelters_col.find({"_id": {"$in": shelter_ids}}, {"name": 1, "city": 1}))
    except (KeyError, TypeError, AttributeError):
        return pets

    smap = {d["_id"]: d for d in docs if "_id" in d}
    for p in pets:
        sid = p.get("shelter_id")
        if sid and sid in smap:
            p["shelter_name"] = smap[sid].get("name")
            p["shelter_city"] = smap[sid].get("city")
    return pets


def get_newest_available_pets(
    constraints: Dict[str, Any],
    top_k: int = 5,
    db: Optional[Database] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve the most recently listed available pets matching core safety/species filters,
    sorted by listed_at descending. Used by the 'New arrivals / just listed' chat path.
    """
    if db is None:
        db = get_sync_db()

    pets_col = db["pets"]
    core_constraints = {
        k: v for k, v in constraints.items()
        if k in ("species", "has_children", "has_other_pets", "allergies")
    }
    mql_filter = build_mql_prefilter(core_constraints)
    candidates = list(pets_col.find(mql_filter))
    candidates.sort(
        key=lambda p: str(p.get("listed_at") or p.get("updated_at") or ""),
        reverse=True,
    )
    cleaned: List[Dict[str, Any]] = []
    for pet in candidates[:top_k]:
        p = dict(pet)
        p.pop("embedding", None)
        p.setdefault("score", 0.9)
        cleaned.append(p)
    return _attach_shelter_metadata(cleaned, db)
