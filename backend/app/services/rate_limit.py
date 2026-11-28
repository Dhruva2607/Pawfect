"""
In-process rate limiting for Gemini-backed endpoints.

Every call to POST /adoptions/apply, POST /chat/message,
POST /matches/direct-eval and POST /shelters/me/pets/{id}/retry-embedding can
fan out to the Google API. Without a guard, a retry loop or a stuck client burns
the API quota. This module provides a small sliding-window limiter.

Scope note: state is per-process. Run the API with a single worker (the default
in the project docs) or move the counters to Redis before scaling out.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from fastapi import HTTPException, status

DEFAULT_WINDOW_SECONDS = 60.0


class SlidingWindowLimiter:
    """Allows at most `limit` events per `window_seconds` for a given key."""

    def __init__(self, limit: int, window_seconds: float = DEFAULT_WINDOW_SECONDS) -> None:
        self._limit = limit
        self._window = window_seconds
        self._events: Dict[str, Deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        """Raise HTTP 429 when `key` exceeds its allowance."""
        now = time.monotonic()
        events = self._events[key]

        cutoff = now - self._window
        while events and events[0] <= cutoff:
            events.popleft()

        if len(events) >= self._limit:
            retry_after = int(self._window - (now - events[0])) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Too many requests. Please wait {retry_after} second(s) "
                    "before trying again."
                ),
                headers={"Retry-After": str(retry_after)},
            )

        events.append(now)

    def reset(self, key: str | None = None) -> None:
        """Clear counters (used by tests)."""
        if key is None:
            self._events.clear()
        else:
            self._events.pop(key, None)


# Chat is the primary user-facing flow. The limit has to sit comfortably above
# what a genuine conversation produces — an adoption interview runs 10-25 turns,
# and a user may retry a few times — otherwise ordinary use gets a 429 and the
# app reports it as "could not connect". 120/min still stops a runaway loop.
chat_limiter = SlidingWindowLimiter(limit=120, window_seconds=60.0)

# Direct evaluation is invoked per pet from the compatibility screen; opening a
# handful of pets should never be limited.
eval_limiter = SlidingWindowLimiter(limit=60, window_seconds=60.0)

# Applications and embedding retries each trigger a model call and are far less
# frequent, so a tighter bound is appropriate.
apply_limiter = SlidingWindowLimiter(limit=30, window_seconds=60.0)
embedding_limiter = SlidingWindowLimiter(limit=30, window_seconds=60.0)


def rate_limit(limiter: SlidingWindowLimiter, key: str) -> None:
    """Convenience wrapper used by routers."""
    limiter.check(key)


# ── Per-shelter embeddings limiter ───────────────────────────────────

def shelter_key(shelter_id: str, action: str) -> str:
    return f"shelter:{shelter_id}:{action}"


def adopter_key(user_id: str, action: str) -> str:
    return f"adopter:{user_id}:{action}"


def pair_key(left: str, right: str) -> Tuple[str, str]:
    return (left, right)
