"""Tests for the adopter-side adoption tracker (P5)."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app import main
from app.routers import adoptions as adoptions_router


class FakeCursor:
    def __init__(self, docs):
        self.docs = list(docs)

    def sort(self, key, direction=1):
        self.docs.sort(key=lambda d: d.get(key) or datetime.min.replace(tzinfo=timezone.utc),
                       reverse=(direction < 0))
        return self

    def skip(self, n):
        self.docs = self.docs[n:]
        return self

    def limit(self, n):
        self.docs = self.docs[:n]
        return self

    async def to_list(self, length):
        return list(self.docs[:length])


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = list(docs or [])

    async def find_one(self, query, *a, **k):
        for doc in self.docs:
            if all(doc.get(key) == val for key, val in query.items()):
                return dict(doc)
        return None

    def find(self, query=None, *a, **k):
        query = query or {}
        return FakeCursor([d for d in self.docs if all(d.get(k2) == v for k2, v in query.items())])


class FakeDatabase:
    def __init__(self, collections):
        self._collections = collections

    def __getitem__(self, name):
        return self._collections.setdefault(name, FakeCollection())


def bearer(user_id: str) -> dict:
    return {"Authorization": f"Bearer token_{user_id}"}


def _now():
    return datetime.now(timezone.utc)


def _make_app(app_id, user_id, pet_name, stage, updated):
    return {
        "_id": app_id,
        "user_id": user_id,
        "pet_id": f"pet_for_{app_id}",
        "pet_name": pet_name,
        "stage_status": stage,
        "applicant_name": "Test Adopter",
        "stage_history": [],
        "submitted_at": updated,
        "updated_at": updated,
    }


def _setup(monkeypatch):
    db = FakeDatabase({
        "adoption_applications": FakeCollection([
            _make_app("app_1", "user_alice", "Buddy", "apply", _now().replace(year=2026, month=1, day=1)),
            _make_app("app_2", "user_alice", "Milo", "review", _now().replace(year=2026, month=2, day=1)),
            _make_app("app_3", "user_alice", "Nala", "adopt", _now().replace(year=2026, month=3, day=1)),
            _make_app("app_4", "user_bob", "Zoe", "apply", _now().replace(year=2026, month=4, day=1)),
        ]),
    })
    monkeypatch.setattr(adoptions_router, "get_async_db", lambda: db)
    return db


def test_mine_requires_credentials(monkeypatch):
    _setup(monkeypatch)
    with TestClient(main.app) as client:
        assert client.get("/api/v1/adoptions/mine").status_code == 401


def test_mine_returns_only_own_applications(monkeypatch):
    _setup(monkeypatch)
    with TestClient(main.app) as client:
        res = client.get("/api/v1/adoptions/mine", headers=bearer("user_alice"))
        assert res.status_code == 200
        ids = [a["application_id"] for a in res.json()]
        assert set(ids) == {"app_1", "app_2", "app_3"}
        assert "app_4" not in ids


def test_mine_is_newest_first(monkeypatch):
    _setup(monkeypatch)
    with TestClient(main.app) as client:
        res = client.get("/api/v1/adoptions/mine", headers=bearer("user_alice"))
        assert res.status_code == 200
        assert [a["application_id"] for a in res.json()] == ["app_3", "app_2", "app_1"]


def test_mine_returns_empty_list_for_new_adopter(monkeypatch):
    _setup(monkeypatch)
    with TestClient(main.app) as client:
        res = client.get("/api/v1/adoptions/mine", headers=bearer("user_new"))
        assert res.status_code == 200
        assert res.json() == []


def test_mine_route_does_not_shadow_status_route(monkeypatch):
    """`/mine` must not be captured by `/{id}/status`; both must resolve."""
    _setup(monkeypatch)
    with TestClient(main.app) as client:
        mine = client.get("/api/v1/adoptions/mine", headers=bearer("user_alice"))
        status = client.get("/api/v1/adoptions/app_1/status", headers=bearer("user_alice"))

        assert mine.status_code == 200
        assert isinstance(mine.json(), list)
        assert status.status_code == 200
        assert status.json()["application_id"] == "app_1"


def test_mine_includes_stage_and_score_fields(monkeypatch):
    _setup(monkeypatch)
    with TestClient(main.app) as client:
        res = client.get("/api/v1/adoptions/mine", headers=bearer("user_alice"))
        body = res.json()
        first = body[0]
        assert "stage_status" in first
        assert "pet_name" in first
        assert first["stage_status"] == "adopt"
