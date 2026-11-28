"""
Seed a rich, deterministic, internally consistent DEMO DATASET for PawFect.

Usage:
    python -m app.scripts.seed_demo_data [flags]

Flags:
    --dry-run           Print what would be written, with counts, and write nothing.
    --reset-demo        Delete ONLY documents carrying `seed_source: "demo_v1"`, then re-seed.
    --skip-embeddings   Seed without calling Gemini; marks new pets `embedding_pending=True`.
    --live-sync-check   Run API-level sync verification against a running backend.
    --yes               Skip confirmation prompt.
    --force             Override production database name guard.
    --seed N            Set random seed (default: 42).
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import logging
import random
import sys
from typing import Any, Dict, List, Optional, Tuple

from app.config import DATABASE_NAME
from app.database.connection import get_sync_db
from app.database.indexes import setup_atlas_vector_search_index, setup_standard_indexes
from app.models.adoption_application import AdoptionApplication, AdoptionStage, StageHistoryEntry
from app.models.pet import Pet
from app.routers.users import _user_id_for_email
from app.scripts.demo_cast import (
    DEMO_ADOPTERS,
    DEMO_SHELTERS,
    DEMO_SHELTER_PASSWORD,
    FLAGSHIP_ADOPTER_EMAIL,
    SEED_SOURCE,
)
from app.scripts.seed_pets import RAW_PET_RECORDS
from app.services.auth import hash_password
from app.services.compatibility import compute_heuristic_compatibility
from app.services.embedding import VECTOR_DIMENSION, generate_embedding
from app.services.matching_schema import (
    MATCHING_DIMENSIONS,
    compute_age_group,
    get_chat_question_flow,
)
from app.services.pet_embeddings import create_pet_embedding_text
from app.services.retrieval import build_mql_prefilter, hybrid_search_pets

logger = logging.getLogger("seed_demo_data")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

REFERENCE_NOW = datetime(2026, 11, 28, 9, 0, 0, tzinfo=timezone.utc)

# ── Breed & Name Pools ───────────────────────────────────────────────

DOG_BREEDS = [
    ("Indian Pariah (Indie)", "medium", (30, 48)),
    ("Beagle", "small", (20, 28)),
    ("Golden Retriever", "large", (55, 72)),
    ("Labrador Retriever", "large", (58, 75)),
    ("Cocker Spaniel", "medium", (24, 32)),
    ("Pug", "small", (14, 19)),
    ("Shih Tzu", "small", (10, 16)),
    ("Poodle (Miniature)", "small", (12, 18)),
    ("Dachshund", "small", (14, 22)),
    ("Rajapalayam", "large", (55, 68)),
    ("Mudhol Hound", "large", (48, 62)),
    ("German Shepherd", "large", (60, 80)),
    ("Bichon Frise", "small", (11, 16)),
    ("Boxer", "large", (55, 70)),
]

CAT_BREEDS = [
    ("Indian Billi (Domestic Shorthair)", "small", (7, 11)),
    ("Bombay Mix", "small", (8, 12)),
    ("Siamese Mix", "small", (8, 11)),
    ("Persian Mix", "medium", (9, 13)),
    ("Maine Coon Mix", "large", (13, 19)),
    ("Bengal Mix", "medium", (10, 14)),
    ("Russian Blue Mix", "small", (8, 12)),
    ("Tabby Shorthair", "medium", (9, 13)),
]

UNIQUE_PET_NAMES = [
    "Aasha", "Aloo", "Amara", "Apollo", "Arlo", "Ash", "Aspen", "Atlas",
    "Bagel", "Baloo", "Bambi", "Bandit", "Barfi", "Basil", "Bean", "Biscuit",
    "Blaze", "Blue", "Boba", "Bolt", "Bramble", "Bree", "Brioche", "Bruno",
    "Bubbles", "Buck", "Butter", "Button", "Cactus", "Cashew", "Cedar", "Chai",
    "Champ", "Chiku", "Chilli", "Chip", "Churro", "Cinder", "Clover", "Cobalt",
    "Cocoa", "Comet", "Cookie", "Copper", "Coral", "Cosmo", "Cricket", "Crumble",
    "Dahlia", "Dash", "Dew", "Doodle", "Dory", "Dusk", "Echo", "Elmo",
    "Ember", "Fable", "Fern", "Fig", "Finch", "Fizz", "Flint", "Flora",
    "Fudge", "Ganga", "Ghibli", "Ginger", "Gizmo", "Gnocchi", "Goose", "Granola",
    "Gully", "Hazel", "Hera", "Honey", "Huckle", "Idli", "Indigo", "Isha",
    "Jalebi", "Jasper", "Jinx", "Juno", "Kaju", "Kaveri", "Kesar", "Kiki",
    "Kulfi", "Ladoo", "Lassi", "Latte", "Lemon", "Lilo", "Lotus", "Lychee",
    "Mango", "Maple", "Marigold", "Miso", "Mocha", "Momo", "Moti", "Muffin",
    "Nala", "Nutmeg", "Oatmeal", "Olive", "Onyx", "Oreo", "Pebble", "Pecan",
    "Pepper", "Pickle", "Pippin", "Pistachio", "Plum", "Pochi", "Pomelo", "Poppy",
    "Praline", "Pudding", "Puri", "Quill", "Ragi", "Raisin", "Rasmalai", "Reed",
    "River", "Roo", "Rumi", "Saffron", "Samosa", "Sesame", "Shadow", "Simba",
    "Sora", "Sprout", "Sundae", "Tamarind", "Tofu", "Toffee", "Tulsi", "Waffles",
    "Walnut", "Willow", "Yuki", "Zazu", "Zephyr", "Zoya",
]


def _deterministic_vector(key: str) -> List[float]:
    """Deterministic unit-ish 768-dim fallback vector for dry-run / offline tests."""
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    base = [(digest[i % len(digest)] / 255.0) - 0.5 for i in range(VECTOR_DIMENSION)]
    return [round(v, 5) for v in base]


# ── 1. Shelter Generator ─────────────────────────────────────────────

def build_demo_shelters(now: datetime = REFERENCE_NOW) -> List[Dict[str, Any]]:
    pw_hash = hash_password(DEMO_SHELTER_PASSWORD)
    shelters: List[Dict[str, Any]] = []
    for idx, spec in enumerate(DEMO_SHELTERS):
        doc = {k: v for k, v in spec.items() if k != "role_summary"}
        doc["password_hash"] = pw_hash
        doc["created_at"] = now - timedelta(days=120 - idx * 10)
        doc["updated_at"] = now - timedelta(days=2)
        doc["seed_source"] = SEED_SOURCE
        shelters.append(doc)
    return shelters


# ── 2. Pet Generator (36 re-homed + 84 new = 120) ────────────────────

def _rehome_shelter_for_seed_pet(pet: Dict[str, Any], idx: int) -> str:
    species = pet.get("species", "dog")
    age_group = pet.get("age_group") or compute_age_group(pet.get("age_months", 24))
    if species == "cat":
        return "shelter_demo_02" if idx % 2 == 0 else "shelter_demo_07"
    if age_group == "senior" or pet.get("special_needs"):
        return "shelter_demo_04"
    if age_group == "puppy_or_kitten":
        return "shelter_demo_05"
    if pet.get("housing_requirement") == "house_with_yard" or pet.get("size") == "large":
        return "shelter_demo_03"
    if pet.get("size") == "small":
        return "shelter_demo_06"
    return "shelter_demo_01" if idx % 2 == 0 else "shelter_demo_07"


def _make_consistent_pet(
    *,
    pet_id: str,
    name: str,
    shelter_id: str,
    species: str,
    breed: str,
    size: str,
    weight_lbs: int,
    age_months: int,
    gender: str,
    energy_level: int,
    grooming_needs: str,
    shedding_level: str,
    noise_level: str,
    alone_time_tolerance: str,
    experience_level_required: str,
    good_with_kids: bool,
    good_with_other_pets: bool,
    housing_requirement: str,
    hypoallergenic: bool,
    special_needs: bool,
    status: str,
    listed_at: datetime,
    updated_at: datetime,
) -> Dict[str, Any]:
    age_group = compute_age_group(age_months)
    coat_type = "curly_hypoallergenic" if hypoallergenic else ("short" if shedding_level == "low" else "medium")

    # Build consistent temperament, quirks, triggers, exercise_needs, and bio_text
    temperament: List[str] = []
    if energy_level >= 4:
        temperament.extend(["Active", "Playful"])
        exercise_needs = "60+ minutes of brisk walks, fetch, or trail runs daily"
    elif energy_level <= 2:
        temperament.extend(["Calm", "Gentle"])
        exercise_needs = "20-30 minutes of gentle strolls and indoor enrichment"
    else:
        temperament.extend(["Balanced", "Affectionate"])
        exercise_needs = "30-45 minutes of daily walks and interactive play"

    if good_with_kids:
        temperament.append("Family Friendly")
    if good_with_other_pets:
        temperament.append("Social")
    if hypoallergenic:
        temperament.append("Hypoallergenic")

    # Bio sentences strictly aligned with numeric/boolean traits
    noise_phrase = {
        "quiet": f"{name} is notably quiet indoors and rarely vocalizes.",
        "moderate": f"{name} has a moderate voice and only speaks up when excited for meals or visitors.",
        "vocal": f"{name} is expressive and vocal, happily chatting with family throughout the day.",
    }[noise_level]

    kids_phrase = (
        f"{name} is patient and gentle around children."
        if good_with_kids
        else f"{name} prefers a calm, adult-only household without young children."
    )

    housing_phrase = (
        f"{name} thrives in a home with a fenced yard for outdoor play."
        if housing_requirement == "house_with_yard"
        else f"{name} adapts smoothly to apartment or townhouse living."
    )

    bio_text = (
        f"{name} is a {age_group.replace('_', ' ')} {breed} with a warm, steady personality. "
        f"{housing_phrase} {noise_phrase} {kids_phrase}"
    )

    quirks = [
        "Tilts head curiously when hearing new sounds",
        "Loves sunbeams near the window after morning meals",
    ]
    triggers = ["Sudden loud fireworks"] if noise_level == "quiet" else ["Unfamiliar delivery scooters"]

    return {
        "_id": pet_id,
        "shelter_id": shelter_id,
        "status": status,
        "listed_at": listed_at,
        "updated_at": updated_at,
        "name": name,
        "species": species,
        "breed": breed,
        "age_months": age_months,
        "age_group": age_group,
        "gender": gender,
        "size": size,
        "weight_lbs": weight_lbs,
        "energy_level": energy_level,
        "grooming_needs": grooming_needs,
        "shedding_level": shedding_level,
        "noise_level": noise_level,
        "alone_time_tolerance": alone_time_tolerance,
        "experience_level_required": experience_level_required,
        "training_level": "well_trained" if experience_level_required == "first_time_friendly" else "basic",
        "coat_type": coat_type,
        "special_needs": special_needs,
        "good_with_kids": good_with_kids,
        "good_with_other_pets": good_with_other_pets,
        "temperament": temperament,
        "housing_requirement": housing_requirement,
        "hypoallergenic": hypoallergenic,
        "bio_text": bio_text,
        "quirks": quirks,
        "exercise_needs": exercise_needs,
        "triggers": triggers,
        "photo_url": "",
        "vaccinated": True,
        "neutered": age_months >= 6,
        "microchipped": True,
        "adoption_fee": 1500.0 if species == "dog" else 1000.0,
        "requires_yard": housing_requirement == "house_with_yard",
        "min_experience": experience_level_required,
        "not_suitable_for_young_children": not good_with_kids,
        "ideal_adopter_notes": "Looking for a committed, loving Bengaluru home.",
        "embedding": None,
        "embedding_pending": True,
        "seed_source": SEED_SOURCE,
    }


def build_demo_pets(rng: random.Random, now: datetime = REFERENCE_NOW) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Returns (rehomed_existing_36, new_demo_84).
    Total = 120 pets with guaranteed coverage matrix & persona match density.
    """
    used_names = set()
    rehomed: List[Dict[str, Any]] = []

    for idx, raw in enumerate(RAW_PET_RECORDS):
        p = deepcopy(raw)
        used_names.add(p["name"])
        p["shelter_id"] = _rehome_shelter_for_seed_pet(p, idx)
        p["status"] = "available"
        p["age_group"] = compute_age_group(p["age_months"])
        listed = now - timedelta(days=rng.randint(10, 85))
        p["listed_at"] = listed
        p["updated_at"] = listed + timedelta(days=rng.randint(0, 5))
        if "hypoallergenic" not in p or p["hypoallergenic"] is None:
            p["hypoallergenic"] = (p.get("shedding_level") == "low")
        p["embedding_pending"] = not bool(p.get("embedding") and len(p["embedding"]) == VECTOR_DIMENSION)
        # Keep existing 36 pets tagged with seed_pets_v1 so --reset-demo never deletes them
        p.setdefault("seed_source", "seed_pets_v1")
        rehomed.append(p)

    # Pick unique names for the 84 new pets
    available_names = [n for n in UNIQUE_PET_NAMES if n not in used_names]
    assert len(available_names) >= 84, "Need at least 84 unique pet names"
    new_names = available_names[:84]

    # Blueprints ensuring:
    # - shelter_demo_01 has 26+ pets total
    # - shelter_demo_08 has 3 pets
    # - Every persona in DEMO_ADOPTERS has >= 3 available matches
    # - Niche combos (senior+large+quiet+apartment) stay at 0-2 matches
    # - 9 pets listed in last 3 days across several shelters
    specs: List[Dict[str, Any]] = []

    def add_spec(shelter_id: str, species: str, **kwargs):
        specs.append({"shelter_id": shelter_id, "species": species, **kwargs})

    # 1) Busiest city shelter (shelter_demo_01): 25 new dogs (+ rehomed = 26+ total)
    for i in range(17):
        # First 6 are adult medium dogs (matches deepika.hasdog & general adopters); next 8 are young small/medium
        is_adult_med = i < 6
        add_spec("shelter_demo_01", "dog", size="medium" if (is_adult_med or i % 2 == 0) else "small",
                 age_months=(42 + i * 4) if is_adult_med else (16 + i * 2),
                 energy_level=3, grooming_needs="low",
                 shedding_level="moderate", noise_level="quiet" if i < 10 else "moderate",
                 alone_time_tolerance="moderate", experience_level_required="first_time_friendly",
                 good_with_kids=True, good_with_other_pets=True, housing_requirement="apartment_or_house")
    for i in range(8):
        add_spec("shelter_demo_01", "dog", size="small", age_months=24 + i * 3, energy_level=2,
                 grooming_needs="low", shedding_level="low", noise_level="quiet",
                 alone_time_tolerance="high", experience_level_required="first_time_friendly",
                 good_with_kids=True, good_with_other_pets=True, housing_requirement="apartment",
                 hypoallergenic=True)

    # 2) Cat-focused rescue (shelter_demo_02): 10 cats (adult small, young small, adult medium, vocal)
    for i in range(10):
        # 0-3: adult small quiet high-alone (meera); 4-6: young small quiet high-alone (tanvi); 7-9: adult medium quiet high-alone (nandini)
        if i < 4:
            sz, age_m, ns, exp = "small", 40 + i * 4, "quiet", "first_time_friendly"
        elif i < 7:
            sz, age_m, ns, exp = "small", 18 + (i - 4) * 3, "quiet", "first_time_friendly"
        else:
            sz, age_m, ns, exp = "medium", 44 + (i - 7) * 5, "quiet" if i < 9 else "vocal", "experienced_preferred"
        add_spec("shelter_demo_02", "cat", size=sz,
                 age_months=age_m, energy_level=2,
                 grooming_needs="low", shedding_level="low" if i < 4 else "moderate",
                 noise_level=ns, alone_time_tolerance="high",
                 experience_level_required=exp,
                 good_with_kids=(i % 2 == 0), good_with_other_pets=True,
                 housing_requirement="apartment", hypoallergenic=(i < 4))

    # 3) Rural big-yard working dogs (shelter_demo_03): 10 large/active yard dogs (5 young + 5 adult)
    for i in range(10):
        add_spec("shelter_demo_03", "dog", size="large",
                 age_months=(18 + i * 2) if i < 5 else (40 + (i - 5) * 4),
                 energy_level=4 if i < 7 else 5, grooming_needs="moderate",
                 shedding_level="high" if i < 5 else "moderate",
                 noise_level="moderate" if i < 8 else "vocal",
                 alone_time_tolerance="moderate",
                 experience_level_required="experienced_preferred",
                 good_with_kids=(i < 5), good_with_other_pets=(i < 7),
                 housing_requirement="house_with_yard")

    # 4) Senior & special-needs sanctuary (shelter_demo_04): 10 pets
    for i in range(10):
        sp = "dog" if i < 6 else "cat"
        add_spec("shelter_demo_04", sp, size="small" if i < 8 else "medium",
                 age_months=90 + i * 4, energy_level=1 if i < 5 else 2,
                 grooming_needs="low" if i < 6 else "high",
                 shedding_level="low" if i < 4 else "moderate",
                 noise_level="quiet", alone_time_tolerance="moderate",
                 experience_level_required="first_time_friendly" if i < 5 else "experienced_preferred",
                 good_with_kids=False if i < 3 else True, good_with_other_pets=True,
                 housing_requirement="apartment_or_house", special_needs=(i % 2 == 0),
                 hypoallergenic=(i < 3))

    # 5) Puppy & kitten foster network (shelter_demo_05): 10 pets (<12 months)
    for i in range(10):
        sp = "dog" if i < 5 else "cat"
        add_spec("shelter_demo_05", sp, size="small", age_months=3 + (i % 7),
                 energy_level=3 if sp == "cat" else 4, grooming_needs="moderate",
                 shedding_level="moderate", noise_level="moderate",
                 alone_time_tolerance="low", experience_level_required="first_time_friendly",
                 good_with_kids=True, good_with_other_pets=True,
                 housing_requirement="apartment_or_house")

    # 6) Toy & small breed rescue (shelter_demo_06): 8 small/hypoallergenic dogs
    for i in range(8):
        add_spec("shelter_demo_06", "dog", size="small", age_months=20 + i * 4,
                 energy_level=2 if i < 4 else 3, grooming_needs="moderate",
                 shedding_level="low", noise_level="quiet",
                 alone_time_tolerance="moderate", experience_level_required="first_time_friendly",
                 good_with_kids=True, good_with_other_pets=True,
                 housing_requirement="apartment", hypoallergenic=True)

    # 7) Family-friendly community shelter (shelter_demo_07): 8 balanced dogs & cats
    for i in range(8):
        sp = "dog" if i < 5 else "cat"
        add_spec("shelter_demo_07", sp, size="medium" if sp == "dog" else "small",
                 age_months=(16 + i * 3) if sp == "dog" else (40 + (i - 5) * 4),
                 energy_level=(3 if i < 5 else 4) if sp == "dog" else 2,
                 grooming_needs="moderate" if sp == "dog" else "low",
                 shedding_level="moderate",
                 noise_level="moderate" if sp == "dog" else "quiet",
                 alone_time_tolerance="moderate",
                 experience_level_required="first_time_friendly",
                 good_with_kids=True, good_with_other_pets=True,
                 housing_requirement="house_with_yard" if i < 4 else "apartment_or_house")

    # 8) Newly registered unverified shelter (shelter_demo_08): 3 pets
    for i in range(3):
        add_spec("shelter_demo_08", "dog" if i < 2 else "cat",
                 size="small" if i == 2 else "medium", age_months=18 + i * 6,
                 energy_level=3, grooming_needs="low", shedding_level="moderate",
                 noise_level="quiet", alone_time_tolerance="moderate",
                 experience_level_required="first_time_friendly",
                 good_with_kids=True, good_with_other_pets=True,
                 housing_requirement="apartment_or_house")

    assert len(specs) == 84, f"Expected 84 new pet specs, got {len(specs)}"

    # Assign statuses: 8 pending, 10 adopted, 3 hidden, 2 draft, rest available (61 available + 36 rehomed = 97 available)
    # Keep shelter_demo_08 all available (3 pets, 0 pending/adopted so empty inbox!)
    non_ecity_indices = [i for i, s in enumerate(specs) if s["shelter_id"] != "shelter_demo_08"]
    rng.shuffle(non_ecity_indices)
    pending_idx = set(non_ecity_indices[:8])
    adopted_idx = set(non_ecity_indices[8:18])
    hidden_idx = set(non_ecity_indices[18:21])
    draft_idx = set(non_ecity_indices[21:23])

    # Pick 9 available pets across several shelters for "New arrivals" (listed within last 3 days)
    available_indices = [i for i in range(len(specs)) if i not in pending_idx | adopted_idx | hidden_idx | draft_idx]
    new_arrival_idx = set(available_indices[:9])

    # Build species-matched photo URL pools from existing RAW_PET_RECORDS
    _broken_urls = {"photo-1513360309081-38a60b9d997c", "photo-1529429617124-95b104e86bcd"}
    dog_photos = [
        r["photo_url"] for r in RAW_PET_RECORDS
        if r.get("species") == "dog" and r.get("photo_url") and not any(b in r["photo_url"] for b in _broken_urls)
    ]
    cat_photos = [
        r["photo_url"] for r in RAW_PET_RECORDS
        if r.get("species") == "cat" and r.get("photo_url") and not any(b in r["photo_url"] for b in _broken_urls)
    ]

    new_pets: List[Dict[str, Any]] = []
    for i, sp in enumerate(specs):
        species = sp["species"]
        breed_pool = [b for b in (DOG_BREEDS if species == "dog" else CAT_BREEDS) if b[1] == sp["size"]]
        if not breed_pool:
            breed_pool = DOG_BREEDS if species == "dog" else CAT_BREEDS
        breed, _, (w_min, w_max) = breed_pool[i % len(breed_pool)]
        weight_lbs = rng.randint(w_min, w_max)

        if i in pending_idx:
            status = "pending"
        elif i in adopted_idx:
            status = "adopted"
        elif i in hidden_idx:
            status = "hidden"
        elif i in draft_idx:
            status = "draft"
        else:
            status = "available"

        if i in new_arrival_idx:
            listed_at = now - timedelta(hours=rng.randint(4, 66))
        else:
            listed_at = now - timedelta(days=rng.randint(5, 88))
        updated_at = listed_at + timedelta(hours=rng.randint(1, 24))

        pet_doc = _make_consistent_pet(
            pet_id=f"pet_demo_{i + 1:03d}",
            name=new_names[i],
            shelter_id=sp["shelter_id"],
            species=species,
            breed=breed,
            size=sp["size"],
            weight_lbs=weight_lbs,
            age_months=sp["age_months"],
            gender="Female" if i % 2 == 0 else "Male",
            energy_level=sp["energy_level"],
            grooming_needs=sp["grooming_needs"],
            shedding_level=sp["shedding_level"],
            noise_level=sp["noise_level"],
            alone_time_tolerance=sp["alone_time_tolerance"],
            experience_level_required=sp["experience_level_required"],
            good_with_kids=sp["good_with_kids"],
            good_with_other_pets=sp["good_with_other_pets"],
            housing_requirement=sp["housing_requirement"],
            hypoallergenic=sp.get("hypoallergenic", False),
            special_needs=sp.get("special_needs", False),
            status=status,
            listed_at=listed_at,
            updated_at=updated_at,
        )
        photo_pool = dog_photos if species == "dog" else cat_photos
        if photo_pool:
            pet_doc["photo_url"] = photo_pool[i % len(photo_pool)]
        new_pets.append(pet_doc)

    return rehomed, new_pets


# ── 3. Users, Chat Sessions, Match Evaluations ───────────────────────

def _build_conversation_for_adopter(
    adopter: Dict[str, Any],
    now: datetime,
) -> Tuple[List[Dict[str, str]], Dict[str, Any], bool]:
    """Generate realistic 1-question-at-a-time conversation history using matching_schema."""
    flow = get_chat_question_flow()
    prefs = adopter.get("chat_prefs", {})
    constraints: Dict[str, Any] = {
        "housing_type": adopter["housing_type"],
        "has_children": adopter["has_children"],
        "has_other_pets": adopter["has_other_pets"],
        "energy_budget": adopter["energy_budget"],
    }
    history: List[Dict[str, str]] = []
    is_complete = adopter.get("chat_status") == "complete"
    max_turns = len(flow) if is_complete else adopter.get("incomplete_step", 3)

    turn_idx = 0
    for field, question, quick_replies in flow:
        if field in ("housing_type", "has_children", "has_other_pets", "energy_budget"):
            continue
        if turn_idx >= max_turns:
            break
        val = prefs.get(field)
        if val is None and not is_complete:
            break
        ts = (now - timedelta(days=3, minutes=(20 - turn_idx))).isoformat()
        history.append({"role": "assistant", "content": question, "timestamp": ts})
        reply = quick_replies[0]
        if field == "species":
            reply = "Looking for a Dog" if val == "dog" else ("Looking for a Cat" if val == "cat" else "Open to either")
        elif field == "allergies":
            reply = "Yes, need low-shedding" if val else "No allergies"
        history.append({"role": "user", "content": reply, "timestamp": ts})
        if val is not None:
            constraints[field] = val
        turn_idx += 1

    return history, constraints, is_complete


class _InMemoryPetsCol:
    """Minimal PyMongo-compatible in-memory pets collection for deterministic retrieval."""

    def __init__(self, docs: List[Dict[str, Any]]):
        self.docs = docs

    def aggregate(self, pipeline):
        from pymongo.errors import OperationFailure
        raise OperationFailure("In-memory seed evaluation", 8000)

    def _match(self, doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
        for k, v in query.items():
            if k == "$or":
                if not any(self._match(doc, clause) for clause in v):
                    return False
            elif isinstance(v, dict):
                if "$in" in v and doc.get(k) not in v["$in"]:
                    return False
                if "$lte" in v:
                    val = doc.get(k)
                    if val is None or val > v["$lte"]:
                        return False
            else:
                if doc.get(k) != v:
                    return False
        return True

    def find(self, query: Dict[str, Any]):
        return [d for d in self.docs if self._match(d, query)]


class _InMemoryDB:
    def __init__(self, pets: List[Dict[str, Any]], shelters: List[Dict[str, Any]]):
        self.cols = {
            "pets": _InMemoryPetsCol(pets),
            "shelters": _InMemoryPetsCol(shelters),
        }

    def __getitem__(self, name: str):
        return self.cols[name]


def build_demo_users_and_sessions(
    rng: random.Random,
    all_pets: List[Dict[str, Any]],
    shelters: List[Dict[str, Any]],
    now: datetime = REFERENCE_NOW,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    available_pets = [p for p in all_pets if p["status"] == "available"]
    adopted_pets = [p for p in all_pets if p["status"] == "adopted"]

    # Ensure every pet has a deterministic vector in memory for hybrid_search_pets
    pets_for_search = []
    for p in all_pets:
        copy_p = dict(p)
        if not copy_p.get("embedding") or len(copy_p["embedding"]) != VECTOR_DIMENSION:
            copy_p["embedding"] = _deterministic_vector(copy_p["_id"])
        pets_for_search.append(copy_p)

    in_mem_db = _InMemoryDB(pets_for_search, shelters)

    users: List[Dict[str, Any]] = []
    sessions: List[Dict[str, Any]] = []
    evaluations: List[Dict[str, Any]] = []

    for idx, adopter in enumerate(DEMO_ADOPTERS):
        uid = _user_id_for_email(adopter["email"])
        is_flagship = adopter["email"] == FLAGSHIP_ADOPTER_EMAIL

        # Saved pets: 2-4 available pets; flagship also gets 1 deliberate adopted (stale) pet
        saved_ids = [p["_id"] for p in rng.sample(available_pets, k=3)]
        if is_flagship and adopted_pets:
            saved_ids.append(adopted_pets[0]["_id"])

        users.append({
            "_id": uid,
            "name": adopter["name"],
            "email": adopter["email"],
            "avatar_url": "",
            "housing_type": adopter["housing_type"],
            "has_children": adopter["has_children"],
            "has_other_pets": adopter["has_other_pets"],
            "energy_budget": adopter["energy_budget"],
            "saved_pets": saved_ids,
            "created_at": now - timedelta(days=45 - idx),
            "updated_at": now - timedelta(days=1),
            "seed_source": SEED_SOURCE,
        })

        chat_status = adopter.get("chat_status", "none")
        if chat_status in ("complete", "incomplete"):
            history, constraints, is_complete = _build_conversation_for_adopter(adopter, now)
            sess_id = f"sess_demo_{idx + 1:03d}"
            sessions.append({
                "_id": sess_id,
                "user_id": uid,
                "conversation_history": history,
                "extracted_constraints": constraints,
                "state_checkpoint": {"is_complete": is_complete},
                "created_at": now - timedelta(days=5),
                "updated_at": now - timedelta(days=2),
                "seed_source": SEED_SOURCE,
            })

            if is_complete:
                # Run REAL hybrid_search_pets against in-memory DB (mocking generate_embedding locally)
                import app.services.retrieval as retrieval_mod
                orig_gen = retrieval_mod.generate_embedding
                retrieval_mod.generate_embedding = lambda q: _deterministic_vector(q)
                try:
                    top3 = hybrid_search_pets(
                        query_text=f"{constraints.get('species', 'pet')} {constraints.get('housing_type', 'home')}",
                        constraints=constraints,
                        top_k=3,
                        db=in_mem_db,  # type: ignore[arg-type]
                    )
                finally:
                    retrieval_mod.generate_embedding = orig_gen

                scored = []
                for p_doc in top3:
                    ev = compute_heuristic_compatibility(Pet(**p_doc), constraints)
                    scored.append((p_doc, ev))
                scored.sort(key=lambda x: x[1].compatibility_score, reverse=True)

                hero_name = scored[0][0]["name"] if scored else "top match"
                for rank, (p_doc, ev) in enumerate(scored):
                    evaluations.append({
                        "_id": f"eval_{sess_id}_{p_doc['_id']}",
                        "session_id": sess_id,
                        "pet_id": p_doc["_id"],
                        "compatibility_score": ev.compatibility_score,
                        "pros": ev.pros,
                        "caveats": ev.caveats,
                        "reasoning_summary": ev.reasoning_summary,
                        "comparison_to_hero": None if rank == 0 else f"Compared to {hero_name}, {p_doc['name']} has slightly different routine needs.",
                        "created_at": now - timedelta(days=2),
                        "seed_source": SEED_SOURCE,
                    })

    return users, sessions, evaluations


# ── 4. Applications & Notifications Generator ────────────────────────

def build_demo_applications_and_notifications(
    rng: random.Random,
    all_pets: List[Dict[str, Any]],
    users: List[Dict[str, Any]],
    now: datetime = REFERENCE_NOW,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Build ~60 logically valid applications and 1-to-1 derived notifications:
    - 10 adopt (1 per adopted pet)
    - 14 review (8 on pending pets + 6 on available pets)
    - 20 apply (unread by shelter)
    - 16 rejected (including competing apps on adopted pets)
    - shelter_demo_01 gets >= 20 apps; shelter_demo_08 gets 0 apps.
    - Flagship adopter has at least 1 apply, 1 review, 1 adopt, 1 rejected.
    """
    flagship = next(u for u in users if u["email"] == FLAGSHIP_ADOPTER_EMAIL)
    other_users = [u for u in users if u["email"] != FLAGSHIP_ADOPTER_EMAIL]
    adopter_prefs_by_uid = {_user_id_for_email(a["email"]): a.get("chat_prefs", {}) for a in DEMO_ADOPTERS}

    adopted_pets = [p for p in all_pets if p["status"] == "adopted"]
    pending_pets = [p for p in all_pets if p["status"] == "pending"]
    available_pets = [p for p in all_pets if p["status"] == "available" and p["shelter_id"] != "shelter_demo_08"]
    # Prioritize shelter_demo_01 pets so it gets 22+ applications
    busiest_avail = [p for p in available_pets if p["shelter_id"] == "shelter_demo_01"]
    other_avail = [p for p in available_pets if p["shelter_id"] != "shelter_demo_01"]

    apps: List[Dict[str, Any]] = []
    notifs: List[Dict[str, Any]] = []
    used_pairs: set[Tuple[str, str]] = set()
    app_counter = 0

    def _pick_user(pet: Dict[str, Any], prefer_user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        candidates = ([prefer_user] if prefer_user else []) + other_users + [flagship]
        for u in candidates:
            if (u["_id"], pet["_id"]) in used_pairs:
                continue
            # Respect kids safety unless no alternative
            if u.get("has_children") and not pet.get("good_with_kids", True):
                continue
            return u
        for u in candidates:
            if (u["_id"], pet["_id"]) not in used_pairs:
                return u
        raise RuntimeError("Exhausted unique (user, pet) pairs")

    def _add_app(
        pet: Dict[str, Any],
        user: Dict[str, Any],
        target_stage: AdoptionStage,
        shelter_note: Optional[str],
        days_ago: int,
        shelter_notif_read: bool,
        adopter_notif_read: bool,
    ):
        nonlocal app_counter
        app_counter += 1
        used_pairs.add((user["_id"], pet["_id"]))
        app_id = f"app_demo_{app_counter:03d}"

        submitted_at = max(pet["listed_at"] + timedelta(hours=2), now - timedelta(days=days_ago))
        if submitted_at > now:
            submitted_at = now - timedelta(hours=1)

        history: List[Dict[str, Any]] = [
            StageHistoryEntry(stage=AdoptionStage.APPLY, timestamp=submitted_at, note="Application submitted").model_dump()
        ]
        updated_at = submitted_at

        if target_stage in (AdoptionStage.REVIEW, AdoptionStage.ADOPT):
            rev_ts = min(now, submitted_at + timedelta(hours=12))
            history.append(StageHistoryEntry(
                stage=AdoptionStage.REVIEW,
                timestamp=rev_ts,
                note=shelter_note if target_stage == AdoptionStage.REVIEW else "Shortlisted for meet & greet",
            ).model_dump())
            updated_at = rev_ts

        if target_stage == AdoptionStage.ADOPT:
            adopt_ts = min(now, updated_at + timedelta(hours=12))
            history.append(StageHistoryEntry(
                stage=AdoptionStage.ADOPT,
                timestamp=adopt_ts,
                note=shelter_note or "Welcome home!",
            ).model_dump())
            updated_at = adopt_ts
        elif target_stage == AdoptionStage.REJECTED:
            rej_ts = min(now, submitted_at + timedelta(hours=18))
            history.append(StageHistoryEntry(
                stage=AdoptionStage.REJECTED,
                timestamp=rej_ts,
                note=shelter_note or "Another match was selected.",
            ).model_dump())
            updated_at = rej_ts

        lifestyle = {
            "housing_type": user["housing_type"],
            "has_children": user["has_children"],
            "has_other_pets": user["has_other_pets"],
            "energy_budget": user["energy_budget"],
            **(adopter_prefs_by_uid.get(user["_id"]) or {}),
        }
        ev = compute_heuristic_compatibility(Pet(**pet), lifestyle)

        apps.append({
            "_id": app_id,
            "user_id": user["_id"],
            "pet_id": pet["_id"],
            "shelter_id": pet["shelter_id"],
            "pet_name": pet["name"],
            "stage_status": target_stage.value,
            "applicant_name": user["name"],
            "applicant_email": user["email"],
            "applicant_phone": "+91-98000-00001",
            "housing_details": f"{user['housing_type'].replace('_', ' ').title()} in Bengaluru",
            "household_members": f"Children: {user['has_children']}, Other pets: {user['has_other_pets']}",
            "notes": f"Excited to meet {pet['name']}!",
            "applicant_lifestyle": lifestyle,
            "compatibility_score": ev.compatibility_score,
            "compatibility_reasoning": ev.reasoning_summary,
            "shelter_note": shelter_note,
            "stage_history": history,
            "submitted_at": submitted_at,
            "updated_at": updated_at,
            "seed_source": SEED_SOURCE,
        })

        # 1) Shelter notification for submission
        notifs.append({
            "_id": f"notif_demo_s_{app_counter:03d}",
            "recipient_role": "shelter",
            "recipient_id": pet["shelter_id"],
            "type": "new_application",
            "title": f"New application for {pet['name']}",
            "message": f"{user['name']} applied to adopt {pet['name']}",
            "pet_id": pet["_id"],
            "pet_name": pet["name"],
            "application_id": app_id,
            "applicant_name": user["name"],
            "read": shelter_notif_read,
            "created_at": submitted_at,
            "seed_source": SEED_SOURCE,
        })

        # 2) Adopter notification for every post-submission stage change
        for h_idx, h in enumerate(history[1:], start=1):
            st = h["stage"].value if isinstance(h["stage"], AdoptionStage) else str(h["stage"])
            note_txt = h.get("note")
            notifs.append({
                "_id": f"notif_demo_a_{app_counter:03d}_{h_idx}",
                "recipient_role": "adopter",
                "recipient_id": user["_id"],
                "type": "application_stage_changed",
                "title": f"Application update for {pet['name']}",
                "message": f"Your adoption application for {pet['name']} is now '{st}'." + (f" Note: {note_txt}" if note_txt else ""),
                "pet_id": pet["_id"],
                "pet_name": pet["name"],
                "application_id": app_id,
                "applicant_name": user["name"],
                "read": adopter_notif_read,
                "created_at": h["timestamp"],
                "seed_source": SEED_SOURCE,
            })

    # 10 ADOPT apps (1 per adopted pet; first goes to flagship)
    for idx, pet in enumerate(adopted_pets):
        u = _pick_user(pet, prefer_user=flagship if idx == 0 else None)
        _add_app(pet, u, AdoptionStage.ADOPT, "Adoption finalized — welcome home!", 10 + idx, True, idx > 0)

    # 8 REVIEW apps (1 per pending pet; first goes to flagship) + 6 REVIEW on available pets = 14 REVIEW
    for idx, pet in enumerate(pending_pets):
        u = _pick_user(pet, prefer_user=flagship if idx == 0 else None)
        _add_app(pet, u, AdoptionStage.REVIEW, "Meet & greet scheduled this weekend.", 4 + idx, True, idx > 0)
    for idx in range(6):
        pet = (busiest_avail + other_avail)[idx]
        u = _pick_user(pet)
        _add_app(pet, u, AdoptionStage.REVIEW, "Home check in progress.", 3 + idx, True, True)

    # 16 REJECTED apps (competing apps on adopted pets + others; first goes to flagship)
    for idx in range(16):
        pet = adopted_pets[idx] if idx < len(adopted_pets) else (busiest_avail + other_avail)[(idx + 6) % len(available_pets)]
        u = _pick_user(pet, prefer_user=flagship if idx == 0 else None)
        note = f"{pet['name']} was adopted by another family." if idx < len(adopted_pets) else "Looking for a home with a fenced yard."
        _add_app(pet, u, AdoptionStage.REJECTED, note, 6 + idx, True, idx > 0)

    # 20 APPLY (new unread apps; first goes to flagship, majority to shelter_demo_01 so it has 22+ apps)
    apply_pool = (busiest_avail * 2) + other_avail
    for idx in range(20):
        pet = apply_pool[idx % len(apply_pool)]
        u = _pick_user(pet, prefer_user=flagship if idx == 0 else None)
        _add_app(pet, u, AdoptionStage.APPLY, None, 1 + (idx % 3), False, True)

    return apps, notifs


# ── 5. Integrity Checks (Section 6) ──────────────────────────────────

def verify_dataset_integrity(
    *,
    shelters: List[Dict[str, Any]],
    pets: List[Dict[str, Any]],
    users: List[Dict[str, Any]],
    sessions: List[Dict[str, Any]],
    evaluations: List[Dict[str, Any]],
    apps: List[Dict[str, Any]],
    notifs: List[Dict[str, Any]],
    skip_embeddings: bool = False,
) -> Dict[str, Any]:
    """Run every Section 6 integrity check; raises AssertionError on any violation."""
    shelter_map = {s["_id"]: s for s in shelters}
    pet_map = {p["_id"]: p for p in pets}
    user_map = {u["_id"]: u for u in users}
    app_map = {a["_id"]: a for a in apps}

    # 1. Foreign keys & denormalized consistency
    for p in pets:
        assert p.get("shelter_id") in shelter_map, f"Pet {p['_id']} references missing shelter {p.get('shelter_id')}"
        assert p["age_group"] == compute_age_group(p["age_months"]), f"Pet {p['_id']} age_group mismatch"
        if not skip_embeddings and p["status"] == "available":
            emb = p.get("embedding")
            assert emb and len(emb) == VECTOR_DIMENSION, f"Available pet {p['_id']} missing 768-dim embedding"
        # Enum checks
        for dim_key, dim in MATCHING_DIMENSIONS.items():
            if dim.is_boolean or dim.is_numeric:
                continue
            val = p.get(dim.pet_field)
            assert val in dim.allowed_pet_values, f"Pet {p['_id']} invalid {dim.pet_field}={val!r}"

    # 2. Applications
    seen_pairs: set[Tuple[str, str]] = set()
    adopted_app_counts: Dict[str, int] = {}
    pending_review_counts: Dict[str, int] = {}

    for a in apps:
        assert a["user_id"] in user_map, f"App {a['_id']} missing user {a['user_id']}"
        assert a["pet_id"] in pet_map, f"App {a['_id']} missing pet {a['pet_id']}"
        pet = pet_map[a["pet_id"]]
        assert a["shelter_id"] == pet["shelter_id"], f"App {a['_id']} shelter_id mismatch"
        assert a["pet_name"] == pet["name"], f"App {a['_id']} pet_name mismatch"
        pair = (a["user_id"], a["pet_id"])
        assert pair not in seen_pairs, f"Duplicate (user, pet) app: {pair}"
        seen_pairs.add(pair)
        assert a["submitted_at"] <= a["updated_at"], f"App {a['_id']} submitted_at > updated_at"
        assert a["stage_history"][-1]["stage"] == a["stage_status"], f"App {a['_id']} history tail mismatch"
        if a["stage_status"] == "adopt":
            adopted_app_counts[pet["_id"]] = adopted_app_counts.get(pet["_id"], 0) + 1
        if a["stage_status"] == "review":
            pending_review_counts[pet["_id"]] = pending_review_counts.get(pet["_id"], 0) + 1

    for p in pets:
        if p["status"] == "adopted":
            assert adopted_app_counts.get(p["_id"], 0) == 1, f"Adopted pet {p['_id']} must have exactly 1 adopt app"
        if p["status"] == "pending":
            assert pending_review_counts.get(p["_id"], 0) == 1, f"Pending pet {p['_id']} must have exactly 1 review app"

    # 3. Saved pets exist
    for u in users:
        for pid in u.get("saved_pets", []):
            assert pid in pet_map, f"User {u['_id']} saved missing pet {pid}"

    # 4. Notifications 1-to-1 with apps & stage_history
    expected_adopter_notifs = sum(max(0, len(a["stage_history"]) - 1) for a in apps)
    shelter_notifs = [n for n in notifs if n["recipient_role"] == "shelter"]
    adopter_notifs = [n for n in notifs if n["recipient_role"] == "adopter"]
    assert len(shelter_notifs) == len(apps), f"Shelter notifs ({len(shelter_notifs)}) != apps ({len(apps)})"
    assert len(adopter_notifs) == expected_adopter_notifs, f"Adopter notifs ({len(adopter_notifs)}) != stage changes ({expected_adopter_notifs})"

    for n in notifs:
        assert n["application_id"] in app_map, f"Notif {n['_id']} missing app"
        assert n["pet_id"] in pet_map, f"Notif {n['_id']} missing pet"
        if n["recipient_role"] == "shelter":
            assert n["recipient_id"] in shelter_map
        else:
            assert n["recipient_id"] in user_map

    # 5. Coverage matrix & persona match density
    covered: Dict[str, set[str]] = {}
    for key, dim in MATCHING_DIMENSIONS.items():
        if dim.is_boolean or dim.is_numeric:
            continue
        vals = {str(p.get(dim.pet_field)) for p in pets}
        missing = set(dim.allowed_pet_values) - vals
        # Note: house_without_yard is an adopter housing_type; pets use apartment / house_with_yard / apartment_or_house
        if key == "housing":
            missing.discard("house_without_yard")
        assert not missing, f"Coverage gap for {key}: missing {missing}"
        covered[key] = vals

    in_mem_col = _InMemoryPetsCol(pets)
    persona_counts: Dict[str, int] = {}
    for adopter in DEMO_ADOPTERS[:15]:
        constraints = {
            "housing_type": adopter["housing_type"],
            "has_children": adopter["has_children"],
            "has_other_pets": adopter["has_other_pets"],
            "energy_budget": adopter["energy_budget"],
            **adopter.get("chat_prefs", {}),
        }
        mql = build_mql_prefilter(constraints)
        assert mql.get("status") == "available"
        matches = in_mem_col.find(mql)
        assert all(m["status"] == "available" for m in matches), "Retrieval returned non-available pet!"
        persona_counts[adopter["email"]] = len(matches)
        assert len(matches) >= 3, f"Persona {adopter['email']} only matched {len(matches)} available pets (need >= 3)"

    # Niche fallback check (senior + large + quiet + apartment should have 0-2 matches)
    niche_mql = build_mql_prefilter({
        "species": "dog",
        "preferred_age_group": "senior",
        "preferred_size": "large",
        "noise_tolerance": "quiet",
        "housing_type": "apartment",
    })
    niche_count = len(in_mem_col.find(niche_mql))
    assert niche_count <= 2, f"Niche combo matched {niche_count} pets; expected <= 2 for fallback testing"

    return {
        "covered_dimensions": {k: sorted(v) for k, v in covered.items()},
        "persona_match_counts": persona_counts,
        "niche_match_count": niche_count,
    }


# ── 6. Live Sync Check (Section 7) ───────────────────────────────────

def run_live_sync_check(base_url: str = "http://localhost:8000/api/v1") -> None:
    """Exercise the REAL running backend API end-to-end and clean up."""
    import requests

    logger.info("Running --live-sync-check against %s ...", base_url)
    # 1. Login as demo shelter 1 and create a pet
    login_res = requests.post(
        f"{base_url}/shelters/auth/login",
        json={"email": DEMO_SHELTERS[0]["email"], "password": DEMO_SHELTER_PASSWORD},
        timeout=15,
    )
    assert login_res.status_code == 200, f"Shelter login failed: {login_res.text}"
    token = login_res.json()["token"]
    shelter_id = login_res.json()["shelter"]["_id"]
    headers = {"Authorization": f"Bearer {token}"}

    unread_before = requests.get(f"{base_url}/notifications/unread-count", headers=headers, timeout=10).json()["unread_count"]

    pet_payload = {
        "name": "SyncCheckPup",
        "species": "dog",
        "breed": "Beagle",
        "age_months": 20,
        "gender": "Female",
        "size": "medium",
        "energy_level": 3,
        "grooming_needs": "low",
        "shedding_level": "moderate",
        "noise_level": "quiet",
        "alone_time_tolerance": "moderate",
        "experience_level_required": "first_time_friendly",
        "good_with_kids": True,
        "good_with_other_pets": True,
        "housing_requirement": "apartment_or_house",
        "hypoallergenic": False,
        "bio_text": "SyncCheckPup is a calm, apartment-friendly beagle created for live sync verification.",
        "status": "available",
    }
    created = requests.post(f"{base_url}/shelters/me/pets", json=pet_payload, headers=headers, timeout=30)
    assert created.status_code == 201, f"Pet create failed: {created.text}"
    pet_id = created.json()["_id"]

    try:
        # Verify visible in GET /pets
        feed = requests.get(f"{base_url}/pets?shelter_id={shelter_id}&limit=100", timeout=15).json()
        assert any(p["_id"] == pet_id for p in feed), "Newly created pet missing from GET /pets"

        # 2. Login as flagship adopter & apply
        adopter_login = requests.post(
            f"{base_url}/users/auth/login",
            json={"email": FLAGSHIP_ADOPTER_EMAIL, "password": "demo"},
            timeout=15,
        ).json()
        user_id = adopter_login["user_id"]

        app_res = requests.post(
            f"{base_url}/adoptions/apply",
            json={
                "user_id": user_id,
                "pet_id": pet_id,
                "applicant_name": adopter_login["name"],
                "applicant_email": FLAGSHIP_ADOPTER_EMAIL,
                "notes": "Live sync verification test",
            },
            timeout=30,
        )
        assert app_res.status_code == 201, f"Apply failed: {app_res.text}"
        app_id = app_res.json()["application_id"]

        unread_after = requests.get(f"{base_url}/notifications/unread-count", headers=headers, timeout=10).json()["unread_count"]
        assert unread_after == unread_before + 1, f"Expected unread_count={unread_before + 1}, got {unread_after}"

        # 3. Move application to review -> adopt
        rev = requests.patch(
            f"{base_url}/shelters/me/applications/{app_id}/stage",
            json={"stage_status": "review", "shelter_note": "Reviewing for sync check"},
            headers=headers,
            timeout=15,
        )
        assert rev.status_code == 200 and rev.json()["stage_status"] == "review"

        adopt = requests.patch(
            f"{base_url}/shelters/me/applications/{app_id}/stage",
            json={"stage_status": "adopt", "shelter_note": "Adopted in sync check"},
            headers=headers,
            timeout=15,
        )
        assert adopt.status_code == 200 and adopt.json()["stage_status"] == "adopt"

        status_check = requests.get(f"{base_url}/adoptions/{app_id}/status", timeout=10).json()
        assert status_check["stage_status"] == "adopt"
        assert status_check["shelter_note"] == "Adopted in sync check"

        # Disappears from GET /pets
        feed_after = requests.get(f"{base_url}/pets/{pet_id}", timeout=10)
        assert feed_after.status_code == 404, "Adopted pet should not be returned by GET /pets/{id}"

        # 4. Edit bio_text as shelter
        upd = requests.put(
            f"{base_url}/shelters/me/pets/{pet_id}",
            json={"bio_text": "Updated bio text for SyncCheckPup to verify embedding regeneration."},
            headers=headers,
            timeout=30,
        )
        assert upd.status_code == 200
        logger.info("Live sync check PASSED all assertions!")
    finally:
        # 5. Clean up test artifacts directly by exact IDs
        db = get_sync_db()
        db["pets"].delete_one({"_id": pet_id})
        db["adoption_applications"].delete_many({"pet_id": pet_id})
        db["notifications"].delete_many({"pet_id": pet_id})
        logger.info("Cleaned up live-sync-check test documents for %s.", pet_id)


# ── 7. Main CLI Entrypoint ───────────────────────────────────────────

def generate_all(seed: int = 42, now: datetime = REFERENCE_NOW) -> Dict[str, Any]:
    rng = random.Random(seed)
    shelters = build_demo_shelters(now)
    rehomed, new_pets = build_demo_pets(rng, now)
    all_pets = rehomed + new_pets
    users, sessions, evaluations = build_demo_users_and_sessions(rng, all_pets, shelters, now)
    apps, notifs = build_demo_applications_and_notifications(rng, all_pets, users, now)
    return {
        "shelters": shelters,
        "rehomed_pets": rehomed,
        "new_pets": new_pets,
        "all_pets": all_pets,
        "users": users,
        "sessions": sessions,
        "evaluations": evaluations,
        "apps": apps,
        "notifs": notifs,
    }


def write_to_db(db: Any, data: Dict[str, Any], *, skip_embeddings: bool = False, reset_demo: bool = False) -> Dict[str, int]:
    if reset_demo:
        for col_name in ("shelters", "pets", "user_profiles", "user_sessions", "match_evaluations", "adoption_applications", "notifications"):
            res = db[col_name].delete_many({"seed_source": SEED_SOURCE})
            logger.info("Deleted %d demo_v1 docs from %s", res.deleted_count, col_name)

    setup_standard_indexes(db)
    setup_atlas_vector_search_index(db)

    # Generate embeddings for pets if not skipping (reusing any valid 768-dim vector already in DB)
    pets_col = db["pets"]
    has_find_one = hasattr(pets_col, "find_one")
    for p in data["all_pets"]:
        if has_find_one and not (p.get("embedding") and len(p["embedding"]) == VECTOR_DIMENSION):
            existing = pets_col.find_one({"_id": p["_id"]}, {"embedding": 1})
            if existing and existing.get("embedding") and len(existing["embedding"]) == VECTOR_DIMENSION:
                p["embedding"] = existing["embedding"]
        has_valid_emb = bool(p.get("embedding") and len(p["embedding"]) == VECTOR_DIMENSION)
        if has_valid_emb:
            p["embedding_pending"] = False
            continue
        if skip_embeddings or p["status"] == "draft":
            p["embedding"] = None
            p["embedding_pending"] = True
        else:
            try:
                p["embedding"] = generate_embedding(create_pet_embedding_text(p))
                p["embedding_pending"] = False
            except Exception as e:
                logger.warning("Embedding failed for %s: %s", p["_id"], e)
                p["embedding"] = None
                p["embedding_pending"] = True
                if p["status"] == "available":
                    p["status"] = "hidden"

    counts: Dict[str, int] = {}
    for col_name, docs in (
        ("shelters", data["shelters"]),
        ("pets", data["all_pets"]),
        ("user_profiles", data["users"]),
        ("user_sessions", data["sessions"]),
        ("match_evaluations", data["evaluations"]),
        ("adoption_applications", data["apps"]),
        ("notifications", data["notifs"]),
    ):
        for doc in docs:
            db[col_name].update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
        counts[col_name] = len(docs)
    return counts


def _print_summary(data: Dict[str, Any], report: Dict[str, Any]) -> None:
    print("\n=== PawFect Demo Dataset Summary ===")
    print(f"Shelters:              {len(data['shelters'])}")
    print(f"Pets (total):          {len(data['all_pets'])} ({len(data['rehomed_pets'])} re-homed + {len(data['new_pets'])} new)")
    status_counts: Dict[str, int] = {}
    for p in data["all_pets"]:
        status_counts[p["status"]] = status_counts.get(p["status"], 0) + 1
    print(f"  Pet statuses:        {status_counts}")
    print(f"Adopter profiles:      {len(data['users'])}")
    print(f"Chat sessions:         {len(data['sessions'])}")
    print(f"Match evaluations:     {len(data['evaluations'])}")
    print(f"Applications:          {len(data['apps'])}")
    app_counts: Dict[str, int] = {}
    for a in data["apps"]:
        app_counts[a["stage_status"]] = app_counts.get(a["stage_status"], 0) + 1
    print(f"  App stages:          {app_counts}")
    print(f"Notifications:         {len(data['notifs'])}")
    print(f"Niche fallback count:  {report['niche_match_count']}")
    print("Persona match counts (sample):")
    for email, cnt in list(report["persona_match_counts"].items())[:6]:
        print(f"  {email}: {cnt} available matches")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Seed PawFect demo dataset into MongoDB.")
    parser.add_argument("--dry-run", action="store_true", help="Print counts & verify integrity without writing.")
    parser.add_argument("--reset-demo", action="store_true", help="Delete only seed_source='demo_v1' docs before seeding.")
    parser.add_argument("--skip-embeddings", action="store_true", help="Skip Gemini embeddings; mark embedding_pending=True.")
    parser.add_argument("--live-sync-check", action="store_true", help="Run Section 7 live API sync verification.")
    parser.add_argument("--yes", action="store_true", help="Skip interactive confirmation prompt.")
    parser.add_argument("--force", action="store_true", help="Override production database name guard.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42).")
    args = parser.parse_args(argv)

    if args.live_sync_check:
        run_live_sync_check()
        return 0

    if "prod" in DATABASE_NAME.lower() and not args.force:
        logger.error("Refusing to run against database '%s' (contains 'prod'). Pass --force to override.", DATABASE_NAME)
        return 1

    data = generate_all(seed=args.seed)
    report = verify_dataset_integrity(
        shelters=data["shelters"],
        pets=data["all_pets"],
        users=data["users"],
        sessions=data["sessions"],
        evaluations=data["evaluations"],
        apps=data["apps"],
        notifs=data["notifs"],
        skip_embeddings=True,  # Pre-write check before Gemini calls
    )
    _print_summary(data, report)

    if args.dry_run:
        print("\n[DRY RUN] Integrity checks passed. No database writes performed.")
        return 0

    print(f"\nTarget database: {DATABASE_NAME}")
    if not args.yes:
        ans = input("Proceed with writing demo dataset to MongoDB? [y/N]: ").strip().lower()
        if ans not in ("y", "yes"):
            print("Aborted.")
            return 0

    db = get_sync_db()
    write_to_db(db, data, skip_embeddings=args.skip_embeddings, reset_demo=args.reset_demo)
    verify_dataset_integrity(
        shelters=data["shelters"],
        pets=data["all_pets"],
        users=data["users"],
        sessions=data["sessions"],
        evaluations=data["evaluations"],
        apps=data["apps"],
        notifs=data["notifs"],
        skip_embeddings=args.skip_embeddings,
    )
    print("\nDemo dataset seeded and verified successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
