"""
SSE heartbeat regression tests.

The model call blocks for several seconds. If the stream stays silent for that
long, an idle timeout can tear it down mid-answer and the app reports a
connection failure. `_generate_sse_stream` now emits `ping` frames while the
turn runs in the background.
"""

import asyncio
import json

import pytest

from app.routers import chat as chat_router


async def _collect(gen, limit=500):
    events = []
    async for item in gen:
        events.append(item)
        if len(events) >= limit:
            break
    return events


def _event_names(events):
    return [e.get("event") for e in events]


@pytest.fixture
def no_persistence(monkeypatch):
    """Skip the Mongo write so these tests stay pure stream tests."""
    async def fake_save(**_kwargs):
        return None

    monkeypatch.setattr(chat_router, "_save_session_data", fake_save)


def test_slow_turn_emits_ping_heartbeats(monkeypatch, no_persistence):
    """A turn that takes ~2.5s must produce several ping frames."""

    def slow_turn(session_id, user_message, history=None, prior_constraints=None):
        import time
        time.sleep(2.5)
        return {
            "response_message": "Here is your answer.",
            "quick_replies": [],
            "is_complete": False,
            "candidate_matches": [],
            "evaluations": [],
            "extracted_constraints": {},
        }

    monkeypatch.setattr(chat_router, "run_matchmaker_turn", slow_turn)

    gen = chat_router._generate_sse_stream(
        session_id="s1",
        user_id="u1",
        user_message="hi",
        history=[],
        prior_constraints={},
    )
    events = asyncio.run(_collect(gen))
    names = _event_names(events)

    assert names[0] == "typing"
    assert names.count("ping") >= 2, f"expected heartbeats, got {names}"
    assert "done" in names
    assert names.index("ping") < names.index("done")


def test_ping_frames_are_well_formed_json(monkeypatch, no_persistence):
    def slow_turn(*_args, **_kwargs):
        import time
        time.sleep(1.4)
        return {
            "response_message": "ok",
            "quick_replies": [],
            "is_complete": False,
            "candidate_matches": [],
            "evaluations": [],
            "extracted_constraints": {},
        }

    monkeypatch.setattr(chat_router, "run_matchmaker_turn", slow_turn)

    gen = chat_router._generate_sse_stream(
        session_id="s2", user_id="u1", user_message="hi",
        history=[], prior_constraints={},
    )
    events = asyncio.run(_collect(gen))

    pings = [e for e in events if e.get("event") == "ping"]
    assert pings, "no ping frames emitted"
    for p in pings:
        payload = json.loads(p["data"])
        assert payload["event"] == "ping"
        assert payload["session_id"] == "s2"


def test_fast_turn_still_completes_without_error(monkeypatch, no_persistence):
    def fast_turn(*_args, **_kwargs):
        return {
            "response_message": "quick",
            "quick_replies": ["A"],
            "is_complete": False,
            "candidate_matches": [],
            "evaluations": [],
            "extracted_constraints": {},
        }

    monkeypatch.setattr(chat_router, "run_matchmaker_turn", fast_turn)

    gen = chat_router._generate_sse_stream(
        session_id="s3", user_id="u1", user_message="hi",
        history=[], prior_constraints={},
    )
    names = _event_names(asyncio.run(_collect(gen)))

    assert names[0] == "typing"
    assert "done" in names
    assert "error" not in names


def test_matches_event_with_mongo_types_is_serializable(monkeypatch, no_persistence):
    """
    Regression: pet documents contain native datetimes and ObjectIds. Emitting a
    `matches` event with them raised
    "TypeError: Object of type datetime is not JSON serializable", which killed
    the stream mid-response and looked like a connection error in the app.
    """
    from datetime import datetime, timezone
    from bson import ObjectId

    def turn_with_mongo_types(*_args, **_kwargs):
        return {
            "response_message": "Here you go.",
            "quick_replies": ["Learn more"],
            "is_complete": True,
            "candidate_matches": [{
                "_id": "pet_1",
                "id": "pet_1",
                "name": "Buddy",
                "species": "dog",
                "listed_at": datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
                "updated_at": datetime(2026, 6, 7, 8, 9, 10, tzinfo=timezone.utc),
                "oid": ObjectId(),
            }],
            "evaluations": [{
                "pet_id": "pet_1",
                "pet_name": "Buddy",
                "compatibility_score": 90,
                "evaluated_at": datetime(2026, 1, 2, tzinfo=timezone.utc),
            }],
            "extracted_constraints": {},
        }

    monkeypatch.setattr(chat_router, "run_matchmaker_turn", turn_with_mongo_types)

    gen = chat_router._generate_sse_stream(
        session_id="s9", user_id="u1", user_message="hi",
        history=[], prior_constraints={},
    )
    events = asyncio.run(_collect(gen))
    names = _event_names(events)

    assert "matches" in names, f"matches event missing: {names}"
    assert "done" in names
    assert "error" not in names

    match_frame = next(e for e in events if e.get("event") == "matches")
    payload = json.loads(match_frame["data"])
    assert payload["candidate_matches"][0]["name"] == "Buddy"
    # datetime must have been rendered as an ISO string, not dropped or crashed
    assert isinstance(payload["candidate_matches"][0]["listed_at"], str)


def test_all_stream_frames_are_valid_json(monkeypatch, no_persistence):
    """Every frame the client receives must parse, or the app shows a parse error."""
    from datetime import datetime, timezone

    def turn(*_args, **_kwargs):
        return {
            "response_message": "ok then",
            "quick_replies": ["A", "B"],
            "is_complete": True,
            "candidate_matches": [{
                "_id": "p1", "name": "Rex", "species": "dog",
                "listed_at": datetime(2026, 3, 4, tzinfo=timezone.utc),
            }],
            "evaluations": [],
            "extracted_constraints": {"species": "dog"},
        }

    monkeypatch.setattr(chat_router, "run_matchmaker_turn", turn)

    gen = chat_router._generate_sse_stream(
        session_id="s10", user_id="u1", user_message="hi",
        history=[], prior_constraints={},
    )
    for frame in asyncio.run(_collect(gen)):
        payload = json.loads(frame["data"])
        assert payload["event"] == frame["event"]


def test_turn_failure_still_reports_error(monkeypatch, no_persistence):
    def broken_turn(*_args, **_kwargs):
        raise RuntimeError("model down")

    monkeypatch.setattr(chat_router, "run_matchmaker_turn", broken_turn)

    gen = chat_router._generate_sse_stream(
        session_id="s4", user_id="u1", user_message="hi",
        history=[], prior_constraints={},
    )
    names = _event_names(asyncio.run(_collect(gen)))

    assert "error" in names
    assert "done" not in names
