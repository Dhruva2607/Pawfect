"""
Tests for P3: honest near-match disclosure, idempotent pet creation,
and Gemini-backed rate limiting.
"""

import pytest
from fastapi import HTTPException

from app.services import nodes
from app.services.rate_limit import SlidingWindowLimiter


# ── Relaxed-match disclosure ─────────────────────────────────────────

def test_relaxed_match_score_is_capped():
    candidates = [{
        "_id": "pet_1",
        "name": "Rex",
        "is_relaxed_match": True,
        "relaxed_fields": ["housing_type"],
    }]
    evaluations = [{
        "pet_id": "pet_1",
        "pet_name": "Rex",
        "compatibility_score": 97,
        "caveats": ["High energy"],
    }]

    result = nodes._apply_relaxed_match_disclosure(evaluations, candidates)

    assert result[0]["compatibility_score"] == nodes.RELAXED_MATCH_SCORE_CAP
    assert result[0]["is_relaxed_match"] is True
    assert "housing type" in " ".join(result[0]["caveats"]).lower()


def test_exact_match_is_not_capped():
    candidates = [{
        "_id": "pet_2",
        "name": "Milo",
        "is_relaxed_match": False,
        "relaxed_fields": [],
    }]
    evaluations = [{
        "pet_id": "pet_2",
        "pet_name": "Milo",
        "compatibility_score": 96,
        "caveats": [],
    }]

    result = nodes._apply_relaxed_match_disclosure(evaluations, candidates)

    assert result[0]["compatibility_score"] == 96
    assert result[0].get("is_relaxed_match") is not True


def test_disclosure_caveat_not_duplicated():
    candidates = [{
        "_id": "pet_3",
        "name": "Nala",
        "is_relaxed_match": True,
        "relaxed_fields": ["energy_budget"],
    }]
    note = "Near match: your energy budget preference differs from this pet."
    evaluations = [{
        "pet_id": "pet_3",
        "pet_name": "Nala",
        "compatibility_score": 80,
        "caveats": [note],
    }]

    result = nodes._apply_relaxed_match_disclosure(evaluations, candidates)

    matching = [c for c in result[0]["caveats"] if "near match" in c.lower()]
    assert len(matching) == 1


def test_disclosure_matches_by_name_when_id_missing():
    candidates = [{
        "_id": "pet_4",
        "name": "Pepper",
        "is_relaxed_match": True,
        "relaxed_fields": ["preferred_size"],
    }]
    evaluations = [{
        "pet_id": "unknown",
        "pet_name": "Pepper",
        "compatibility_score": 90,
        "caveats": [],
    }]

    result = nodes._apply_relaxed_match_disclosure(evaluations, candidates)
    assert result[0]["compatibility_score"] == nodes.RELAXED_MATCH_SCORE_CAP


def test_disclosure_is_noop_for_empty_relaxed_list():
    candidates = [{
        "_id": "pet_5",
        "name": "Zoe",
        "is_relaxed_match": True,
        "relaxed_fields": [],
    }]
    evaluations = [{
        "pet_id": "pet_5",
        "pet_name": "Zoe",
        "compatibility_score": 95,
        "caveats": [],
    }]

    result = nodes._apply_relaxed_match_disclosure(evaluations, candidates)
    # Cap still applies because the pet is flagged relaxed.
    assert result[0]["compatibility_score"] == nodes.RELAXED_MATCH_SCORE_CAP
    assert result[0]["caveats"] == []


# ── Retrieval flags ──────────────────────────────────────────────────

class _StubDb:
    """Minimal stand-in for a PyMongo database handle."""

    def __init__(self):
        self.collections = {}

    def __getitem__(self, name):
        return self.collections.setdefault(name, object())


def test_retrieval_flags_relaxed_matches(monkeypatch):
    """When retrieval must relax constraints, results carry the disclosure flags."""
    from app.services import retrieval

    monkeypatch.setattr(retrieval, "generate_embedding", lambda _t: [0.1] * 768)

    strict_results = []  # strict search finds nothing

    def fake_search(pets_col, query_vector, mql_filter, top_k):
        if mql_filter.get("housing_requirement") or mql_filter.get("energy_level"):
            return []
        return [{"_id": "pet_alt", "name": "Alt", "score": 0.5}]

    monkeypatch.setattr(retrieval, "_run_vector_or_cosine_search", fake_search)
    monkeypatch.setattr(retrieval, "_attach_shelter_metadata", lambda pets, db: pets)

    results = retrieval.hybrid_search_pets(
        query_text="small quiet cat",
        constraints={
            "species": "cat",
            "housing_type": "apartment",
            "energy_budget": 2,
            "preferred_size": "small",
        },
        top_k=3,
        db=_StubDb(),
    )

    assert results, "expected relaxed fallback results"
    assert all(r["is_relaxed_match"] for r in results)
    joined = " ".join(results[0]["relaxed_fields"])
    assert "housing_type" in joined or "energy_budget" in joined or "preferred_size" in joined


def test_retrieval_does_not_flag_exact_matches(monkeypatch):
    from app.services import retrieval

    monkeypatch.setattr(retrieval, "generate_embedding", lambda _t: [0.1] * 768)
    monkeypatch.setattr(
        retrieval,
        "_run_vector_or_cosine_search",
        lambda pets_col, qv, mql, top_k: [{"_id": "pet_exact", "name": "Exact", "score": 0.9}],
    )
    monkeypatch.setattr(retrieval, "_attach_shelter_metadata", lambda pets, db: pets)

    results = retrieval.hybrid_search_pets(
        query_text="cat",
        constraints={"species": "cat"},
        top_k=3,
        db=_StubDb(),
    )

    assert results
    assert results[0]["is_relaxed_match"] is False
    assert results[0]["relaxed_fields"] == []


# ── Rate limiter ─────────────────────────────────────────────────────

def test_limiter_allows_up_to_limit():
    limiter = SlidingWindowLimiter(limit=3, window_seconds=60)
    for _ in range(3):
        limiter.check("key")


def test_limiter_rejects_over_limit():
    limiter = SlidingWindowLimiter(limit=2, window_seconds=60)
    limiter.check("key")
    limiter.check("key")
    with pytest.raises(HTTPException) as exc:
        limiter.check("key")
    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers


def test_limiter_scopes_per_key():
    limiter = SlidingWindowLimiter(limit=1, window_seconds=60)
    limiter.check("a")
    limiter.check("b")  # different key, allowed
    with pytest.raises(HTTPException):
        limiter.check("a")


def test_limiter_reset():
    limiter = SlidingWindowLimiter(limit=1, window_seconds=60)
    limiter.check("a")
    limiter.reset("a")
    limiter.check("a")  # allowed again after reset


def test_limiter_window_expiry(monkeypatch):
    """Events older than the window must not count."""
    limiter = SlidingWindowLimiter(limit=1, window_seconds=1.0)

    clock = {"now": 1000.0}
    monkeypatch.setattr("app.services.rate_limit.time.monotonic", lambda: clock["now"])

    limiter.check("a")
    with pytest.raises(HTTPException):
        limiter.check("a")

    clock["now"] += 2.0  # past the window
    limiter.check("a")


# ── Configured policy (regression) ───────────────────────────────────

def test_chat_limit_comfortably_exceeds_a_real_conversation():
    """
    Regression: the chat limit used to be 20/min, so turn 21 of a normal
    adoption interview returned 429, which the app surfaced as
    "The matchmaker could not connect."

    A realistic session is 10-25 turns; allow well beyond that.
    """
    from app.services import rate_limit

    assert rate_limit.chat_limiter._limit >= 100, (
        f"chat limit {rate_limit.chat_limiter._limit}/min is too low for a "
        "normal conversation and will surface as a connection error"
    )


def test_chat_limiter_allows_a_full_interview(monkeypatch):
    """30 turns in one minute must all be accepted."""
    from app.services import rate_limit

    clock = {"now": 5000.0}
    monkeypatch.setattr("app.services.rate_limit.time.monotonic", lambda: clock["now"])

    limiter = rate_limit.SlidingWindowLimiter(
        limit=rate_limit.chat_limiter._limit,
        window_seconds=rate_limit.chat_limiter._window,
    )

    for turn in range(30):
        clock["now"] += 1.0  # one turn per second, a realistic pace
        limiter.check("adopter:user_x:chat")


def test_chat_limiter_still_stops_a_runaway_loop():
    """The limiter must still protect the API from a tight retry loop."""
    from app.services import rate_limit

    limiter = rate_limit.SlidingWindowLimiter(
        limit=rate_limit.chat_limiter._limit,
        window_seconds=rate_limit.chat_limiter._window,
    )

    for _ in range(rate_limit.chat_limiter._limit):
        limiter.check("adopter:user_x:chat")

    with pytest.raises(HTTPException) as exc:
        limiter.check("adopter:user_x:chat")
    assert exc.value.status_code == 429


def test_apply_limit_allows_reasonable_browsing():
    """Applying to a few pets should never be limited."""
    from app.services import rate_limit

    assert rate_limit.apply_limiter._limit >= 20
    assert rate_limit.eval_limiter._limit >= 40
