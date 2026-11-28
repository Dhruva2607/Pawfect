"""
Coverage test: validates that matching_schema.py is the single source of truth.

Fails if:
1. Any adopter dimension in the chatbot flow has no pet-side field in matching_schema
2. Any matchable pet field is missing from the GET /meta/pet-options endpoint
3. Housing normalization is correct (house_without_yard ≠ yard-requiring pets)
4. Alone-hours → tolerance mapping is correct (6 → high, not 7)
5. Allergy filter uses hypoallergenic bool, not regex

When a new matchable dimension is added later, the chatbot must ask about it
and the shelter form must collect it.
"""

import pytest
from app.services.matching_schema import (
    MATCHING_DIMENSIONS,
    get_adopter_fields,
    get_pet_fields,
    get_chat_question_flow,
    get_pet_options_response,
    compute_age_group,
    map_alone_hours_to_tolerance,
)
from app.services.retrieval import build_mql_prefilter


# ── 1. Every chatbot dimension has a pet-side field ───────────────────

def test_every_chatbot_dimension_has_pet_field():
    """Every adopter dimension in the chatbot question flow has a matching pet-side field."""
    chat_flow = get_chat_question_flow()
    adopter_fields_in_flow = {field for field, _, _ in chat_flow}
    schema_adopter_fields = get_adopter_fields()

    missing = adopter_fields_in_flow - schema_adopter_fields
    assert not missing, (
        f"Chatbot asks about {missing} but matching_schema has no corresponding dimension"
    )


def test_every_schema_dimension_is_in_chatbot_flow():
    """Every dimension in matching_schema appears in the chatbot question flow."""
    chat_flow = get_chat_question_flow()
    adopter_fields_in_flow = {field for field, _, _ in chat_flow}
    schema_adopter_fields = get_adopter_fields()

    missing = schema_adopter_fields - adopter_fields_in_flow
    assert not missing, (
        f"matching_schema defines {missing} but the chatbot never asks about them"
    )


# ── 2. Every matchable pet field is in the meta/pet-options endpoint ──

def test_every_pet_field_in_options_endpoint():
    """Every matchable pet field is exposed in the pet-options endpoint."""
    options = get_pet_options_response()
    pet_fields_in_endpoint = {
        dim_data["pet_field"]
        for dim_data in options["dimensions"].values()
    }
    schema_pet_fields = get_pet_fields()

    missing = schema_pet_fields - pet_fields_in_endpoint
    assert not missing, (
        f"Pet fields {missing} exist in matching_schema but are missing from /meta/pet-options"
    )


def test_every_dimension_has_allowed_values():
    """Every dimension must have at least 2 allowed values or be boolean."""
    for key, dim in MATCHING_DIMENSIONS.items():
        assert len(dim.allowed_pet_values) >= 2, (
            f"Dimension '{key}' has fewer than 2 allowed values: {dim.allowed_pet_values}"
        )


# ── 3. Housing normalization ─────────────────────────────────────────

def test_house_without_yard_does_not_match_yard_pets():
    """house_without_yard must NOT match pets that require house_with_yard."""
    mql = build_mql_prefilter({"housing_type": "house_without_yard"})
    housing_filter = mql.get("housing_requirement", {})
    allowed = housing_filter.get("$in", [])
    assert "house_with_yard" not in allowed, (
        "house_without_yard should NOT include house_with_yard pets"
    )
    assert "apartment" in allowed or "apartment_or_house" in allowed, (
        "house_without_yard should match apartment or apartment_or_house pets"
    )


def test_house_with_yard_matches_yard_pets():
    """house_with_yard should match pets requiring yard or flexible."""
    mql = build_mql_prefilter({"housing_type": "house_with_yard"})
    housing_filter = mql.get("housing_requirement", {})
    allowed = housing_filter.get("$in", [])
    assert "house_with_yard" in allowed
    assert "apartment_or_house" in allowed


def test_apartment_does_not_match_yard_pets():
    """apartment must NOT match pets that require house_with_yard."""
    mql = build_mql_prefilter({"housing_type": "apartment"})
    housing_filter = mql.get("housing_requirement", {})
    allowed = housing_filter.get("$in", [])
    assert "house_with_yard" not in allowed


# ── 4. Alone hours → tolerance mapping ────────────────────────────────

def test_alone_hours_6_maps_to_high():
    """6 hours alone must map to 'high' tolerance (not 7)."""
    mql = build_mql_prefilter({"daily_alone_hours": 6})
    assert mql.get("alone_time_tolerance") == "high", (
        "6+ hours alone should require 'high' tolerance, not 7+"
    )


def test_alone_hours_mapping_function():
    """Verify the mapping function: 0-3→low, 4-5→moderate, 6+→high."""
    assert map_alone_hours_to_tolerance(0) == "low"
    assert map_alone_hours_to_tolerance(3) == "low"
    assert map_alone_hours_to_tolerance(4) == "moderate"
    assert map_alone_hours_to_tolerance(5) == "moderate"
    assert map_alone_hours_to_tolerance(6) == "high"
    assert map_alone_hours_to_tolerance(8) == "high"


def test_alone_hours_4_maps_to_moderate_or_high():
    """4 hours alone should accept moderate or high tolerance pets."""
    mql = build_mql_prefilter({"daily_alone_hours": 4})
    tolerance = mql.get("alone_time_tolerance")
    if isinstance(tolerance, dict):
        allowed = tolerance.get("$in", [])
        assert "moderate" in allowed
        assert "high" in allowed


# ── 5. Allergy filter uses hypoallergenic, not regex ──────────────────

def test_allergy_filter_uses_hypoallergenic_bool():
    """Allergy filter must use hypoallergenic == True, not regex on bio/temperament."""
    mql = build_mql_prefilter({"allergies": True})
    or_clauses = mql.get("$or", [])
    assert len(or_clauses) >= 2, "Allergy filter should have at least 2 OR clauses"

    # Must include hypoallergenic: True
    hypo_clause = {"hypoallergenic": True}
    assert hypo_clause in or_clauses, (
        "Allergy filter must include {hypoallergenic: True}"
    )

    # Must include shedding_level: "low"
    shed_clause = {"shedding_level": "low"}
    assert shed_clause in or_clauses, (
        "Allergy filter must include {shedding_level: 'low'}"
    )

    # Must NOT use $regex on bio_text or temperament
    for clause in or_clauses:
        for key, val in clause.items():
            if isinstance(val, dict) and "$regex" in val:
                pytest.fail(
                    f"Allergy filter must NOT use $regex. Found regex on '{key}': {val}"
                )


# ── 6. Status filter always present ──────────────────────────────────

def test_status_available_always_in_filter():
    """build_mql_prefilter must always include status='available'."""
    mql = build_mql_prefilter({})
    assert mql.get("status") == "available", (
        "build_mql_prefilter must always filter status='available'"
    )


def test_status_available_with_constraints():
    """status='available' present even when other constraints are set."""
    mql = build_mql_prefilter({
        "species": "dog",
        "has_children": True,
        "housing_type": "apartment",
    })
    assert mql.get("status") == "available"


# ── 7. Age group computation ─────────────────────────────────────────

def test_age_group_computation():
    """age_group is computed server-side from age_months."""
    assert compute_age_group(2) == "puppy_or_kitten"
    assert compute_age_group(11) == "puppy_or_kitten"
    assert compute_age_group(12) == "young"
    assert compute_age_group(35) == "young"
    assert compute_age_group(36) == "adult"
    assert compute_age_group(83) == "adult"
    assert compute_age_group(84) == "senior"
    assert compute_age_group(120) == "senior"


# ── 8. Options endpoint structure ────────────────────────────────────

def test_pet_options_has_all_dimensions():
    """pet-options response includes entries for all dimensions + hypoallergenic."""
    options = get_pet_options_response()
    dims = options["dimensions"]
    for key in MATCHING_DIMENSIONS:
        assert key in dims, f"Dimension '{key}' missing from pet-options response"
    assert "hypoallergenic" in dims, "hypoallergenic missing from pet-options response"


def test_pet_options_has_age_group_ranges():
    """pet-options includes age_group range definitions."""
    options = get_pet_options_response()
    ranges = options["age_group_ranges"]
    assert "puppy_or_kitten" in ranges
    assert "young" in ranges
    assert "adult" in ranges
    assert "senior" in ranges


def test_pet_options_has_alone_hours_mapping():
    """pet-options includes alone-hours → tolerance mapping."""
    options = get_pet_options_response()
    mapping = options["alone_hours_mapping"]
    assert mapping["0-3"] == "low"
    assert mapping["4-5"] == "moderate"
    assert mapping["6+"] == "high"
