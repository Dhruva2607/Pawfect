"""
Hybrid Retrieval Service: MQL Pre-filtering combined with Vector Similarity Search.
[FROM MARKDOWN] matches Step 2.3 and Section 3 (MongoDB Atlas Vector Search with hybrid pre-filtering).
"""

import math
import logging
from typing import List, Dict, Any, Optional
from pymongo.database import Database
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

    # Housing requirement filter
    housing = constraints.get("housing_type")
    if housing:
        housing_clean = housing.lower()
        if "apartment" in housing_clean:
            query["housing_requirement"] = {"$in": ["apartment", "apartment_or_house"]}
        elif "yard" in housing_clean:
            # Houses with yard can take apartment_or_house or house_with_yard
            query["housing_requirement"] = {"$in": ["apartment_or_house", "house_with_yard"]}

    # Hypoallergenic filter if allergies are flagged
    if constraints.get("allergies") is True:
        query["$or"] = [
            {"temperament": {"$regex": "hypoallergenic", "$options": "i"}},
            {"temperament": {"$regex": "low shedding", "$options": "i"}},
            {"bio_text": {"$regex": "hypoallergenic", "$options": "i"}},
            {"bio_text": {"$regex": "allergy", "$options": "i"}},
        ]

    return query


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
    4. Returns top_k ranked candidate matches with similarity score.
    """
    if db is None:
        db = get_sync_db()

    pets_col = db["pets"]

    # 1. Generate query embedding vector
    query_vector = generate_embedding(query_text)

    # 2. Build MQL pre-filter
    mql_filter = build_mql_prefilter(constraints)
    logger.info("Executing hybrid search with MQL filter: %s", mql_filter)

    # 3. Try Atlas $vectorSearch pipeline first
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
                    "gender": 1,
                    "size": 1,
                    "energy_level": 1,
                    "good_with_kids": 1,
                    "good_with_other_pets": 1,
                    "temperament": 1,
                    "housing_requirement": 1,
                    "bio_text": 1,
                    "quirks": 1,
                    "exercise_needs": 1,
                    "triggers": 1,
                    "photo_url": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        results = list(pets_col.aggregate(pipeline))
        if results:
            logger.info("Retrieved %d candidates via Atlas $vectorSearch.", len(results))
            return results
    except Exception as e:
        logger.debug("Atlas $vectorSearch pipeline not active on cluster (%s). Falling back to hybrid MQL + cosine ranking.", e)

    # 4. Fallback: MQL pre-filter + in-memory cosine ranking
    candidates_cursor = pets_col.find(mql_filter)
    candidates = list(candidates_cursor)

    # If strict filter returned zero results, relax slightly by keeping only species & kids safety
    if not candidates and mql_filter:
        relaxed_filter: Dict[str, Any] = {}
        if "species" in mql_filter:
            relaxed_filter["species"] = mql_filter["species"]
        if "good_with_kids" in mql_filter:
            relaxed_filter["good_with_kids"] = True
        logger.info("Relaxing MQL filter to: %s", relaxed_filter)
        candidates = list(pets_col.find(relaxed_filter))

    # If still empty, fall back to all pets
    if not candidates:
        candidates = list(pets_col.find({}))

    # Rank by cosine similarity
    ranked: List[Dict[str, Any]] = []
    for pet in candidates:
        emb = pet.get("embedding")
        if emb and len(emb) == 768:
            score = compute_cosine_similarity(query_vector, emb)
        else:
            score = 0.0

        pet_clean = dict(pet)
        pet_clean.pop("embedding", None)  # Remove raw embedding array from candidate representation
        pet_clean["score"] = round(score, 4)
        ranked.append(pet_clean)

    ranked.sort(key=lambda x: x["score"], reverse=True)
    top_candidates = ranked[:top_k]
    logger.info("Retrieved %d candidates via hybrid MQL + cosine ranking.", len(top_candidates))
    return top_candidates

