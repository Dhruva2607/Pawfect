"""
Regression tests for the conversational-intake constraint merge (P2).

The original defect: the intake node merged constraints with
    {**prior, **llm_response}
and the LLM does not echo every known field each turn, so answered dimensions
(notably grooming / noise / alone-hours / experience / allergies) disappeared
from the session. `_next_missing_question` then saw them as unanswered and asked
again — indefinitely.
"""

import pytest

from app.services import nodes
from app.services.nodes import (
    extract_from_replies,
    merge_constraints,
    _repeats_known_constraint,
)
from app.services.state import LifestyleConstraints


# ── merge_constraints ────────────────────────────────────────────────

def test_merge_never_drops_prior_answers():
    prior = {
        "species": "cat",
        "preferred_age_group": "adult",
        "preferred_size": "large",
        "grooming_tolerance": "high",
    }
    # The model only mentions noise this turn.
    new = {"noise_tolerance": "quiet"}
    merged = merge_constraints(prior, new)

    assert merged["species"] == "cat"
    assert merged["preferred_age_group"] == "adult"
    assert merged["preferred_size"] == "large"
    assert merged["grooming_tolerance"] == "high"
    assert merged["noise_tolerance"] == "quiet"


def test_merge_ignores_none_and_empty_values():
    prior = {"species": "dog", "preferred_size": "small"}
    new = {"species": None, "preferred_size": ""}
    merged = merge_constraints(prior, new)
    assert merged["species"] == "dog"
    assert merged["preferred_size"] == "small"


def test_merge_lets_new_value_win_when_meaningful():
    prior = {"species": "dog"}
    merged = merge_constraints(prior, {"species": "cat"})
    assert merged["species"] == "cat"


def test_merge_handles_empty_inputs():
    assert merge_constraints({}, {}) == {}
    assert merge_constraints({"a": 1}, {}) == {"a": 1}
    assert merge_constraints({}, {"a": 1}) == {"a": 1}


# ── extract_from_replies ─────────────────────────────────────────────

@pytest.mark.parametrize("chip,field,value", [
    ("Looking for a Cat", "species", "cat"),
    ("Looking for a Dog", "species", "dog"),
    ("Open to either", "species", "any"),
    ("Adult (3-7 yrs)", "preferred_age_group", "adult"),
    ("Puppy or Kitten", "preferred_age_group", "puppy_or_kitten"),
    ("Senior (7+ yrs)", "preferred_age_group", "senior"),
    ("Any age", "preferred_age_group", "any"),
    ("Small", "preferred_size", "small"),
    ("Any size", "preferred_size", "any"),
    ("Low maintenance", "grooming_tolerance", "low"),
    ("High grooming is fine", "grooming_tolerance", "high"),
    ("Quiet (minimal barking/meowing)", "noise_tolerance", "quiet"),
    ("Vocal pets are fine", "noise_tolerance", "vocal"),
    ("First-time owner", "experience_level", "first_time"),
    ("Experienced owner", "experience_level", "experienced"),
    ("Apartment", "housing_type", "apartment"),
    ("House with yard", "housing_type", "house_with_yard"),
    ("No allergies", "allergies", False),
    ("Yes, need low-shedding", "allergies", True),
    ("0-3 hours", "daily_alone_hours", 2),
    ("6+ hours", "daily_alone_hours", 7),
    ("Calm & low energy", "energy_budget", 2),
])
def test_extract_chip_replies(chip, field, value):
    extracted = extract_from_replies(chip)
    assert extracted.get(field) == value, f"{chip!r} should set {field}={value!r}"


def test_extract_combined_household_chip_sets_both_fields():
    extracted = extract_from_replies("Have children & pets")
    assert extracted["has_children"] is True
    assert extracted["has_other_pets"] is True


def test_extract_none_household_chip_sets_both_false():
    extracted = extract_from_replies("No children or pets")
    assert extracted["has_children"] is False
    assert extracted["has_other_pets"] is False


def test_extract_ignores_unrelated_text():
    assert extract_from_replies("hi") == {}
    assert extract_from_replies("tell me more about Jasper") == {}
    assert extract_from_replies("") == {}


# ── _repeats_known_constraint ────────────────────────────────────────

def test_repeat_detected_for_answered_dimension():
    constraints = {"grooming_tolerance": "high"}
    assert _repeats_known_constraint(
        "What is your grooming tolerance or willingness for coat upkeep?", constraints
    )


def test_no_repeat_when_dimension_unanswered():
    assert not _repeats_known_constraint(
        "What is your grooming tolerance or willingness for coat upkeep?", {}
    )


def test_repeat_detected_for_signup_field():
    constraints = {"housing_type": "apartment"}
    assert _repeats_known_constraint("What kind of living space do you have?", constraints)


# ── End-to-end: the original bug ─────────────────────────────────────

class _StubLLM:
    """Always claims it needs more info and re-asks grooming, like the real model did."""

    def __init__(self, extracted: dict):
        self._extracted = extracted

    def with_structured_output(self, _schema):
        return self

    def invoke(self, _messages):
        return nodes.IntakeAnalysisOutput(
            extracted_constraints=LifestyleConstraints(**self._extracted),
            is_sufficient_for_search=False,
            follow_up_question="What is your grooming tolerance or willingness for coat upkeep?",
            suggested_quick_replies=["Low maintenance", "Moderate brushing", "High grooming is fine"],
        )


def test_answered_grooming_is_not_asked_again(monkeypatch):
    """
    Reproduces the reported defect: the adopter tapped "High grooming is fine",
    then asked a follow-up question and was asked about grooming a second time.
    """
    monkeypatch.setattr(nodes, "get_chat_llm", lambda **_: _StubLLM({"species": "cat"}))

    prior = {
        "species": "cat",
        "preferred_age_group": "adult",
        "preferred_size": "large",
        "housing_type": "apartment",
        "has_children": False,
        "has_other_pets": False,
        "energy_budget": 3,
        "grooming_tolerance": "high",
    }

    result = nodes.conversational_intake_node({
        "user_message": "tell me more about Jasper",
        "conversation_history": [],
        "extracted_constraints": prior,
    })

    # Grooming must survive the turn...
    assert result["extracted_constraints"]["grooming_tolerance"] == "high"
    # ...and must not be asked about again.
    assert "grooming" not in result["response_message"].lower()
    assert "coat upkeep" not in result["response_message"].lower()
    # The retained answers are all still present.
    for key, value in prior.items():
        assert result["extracted_constraints"][key] == value


def test_chip_answer_is_recorded_even_when_llm_omits_it(monkeypatch):
    """
    If the model returns no grooming value but the adopter tapped the chip,
    the chip answer must still be persisted.
    """
    monkeypatch.setattr(nodes, "get_chat_llm", lambda **_: _StubLLM({}))

    result = nodes.conversational_intake_node({
        "user_message": "High grooming is fine",
        "conversation_history": [],
        "extracted_constraints": {"species": "dog"},
    })

    assert result["extracted_constraints"]["grooming_tolerance"] == "high"
    assert result["extracted_constraints"]["species"] == "dog"


def test_all_dimensions_survive_repeated_turns(monkeypatch):
    """Walking the whole flow must never lose a previously supplied answer."""
    monkeypatch.setattr(nodes, "get_chat_llm", lambda **_: _StubLLM({}))

    constraints: dict = {}
    chips = [
        "Looking for a Cat",
        "Adult (3-7 yrs)",
        "Small",
        "Low maintenance",
        "Quiet (minimal barking/meowing)",
        "0-3 hours",
        "First-time owner",
        "Apartment",
        "No allergies",
    ]

    for chip in chips:
        result = nodes.conversational_intake_node({
            "user_message": chip,
            "conversation_history": [],
            "extracted_constraints": constraints,
        })
        constraints = result["extracted_constraints"]

    assert constraints["species"] == "cat"
    assert constraints["preferred_age_group"] == "adult"
    assert constraints["preferred_size"] == "small"
    assert constraints["grooming_tolerance"] == "low"
    assert constraints["noise_tolerance"] == "quiet"
    assert constraints["daily_alone_hours"] == 2
    assert constraints["experience_level"] == "first_time"
    assert constraints["housing_type"] == "apartment"
    assert constraints["allergies"] is False
