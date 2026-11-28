"""
Authorization regression tests (P1).

These lock in the adopter-isolation contract:
- No credentials -> 401
- Another adopter's credentials -> 403
- An unauthenticated ?user_id= query param cannot reach another person's data
- A shelter JWT cannot be used on adopter endpoints
"""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app import main
from app.routers import adoptions as adoptions_router
from app.routers import notifications as notifications_router
from app.routers import users as users_router


class FakeCursor:
    def __init__(self, docs):
        self.docs = list(docs)

    def sort(self, key, direction=1):
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

    async def find_one(self, query, *args, **kwargs):
        for doc in self.docs:
            if self._matches(doc, query):
                return dict(doc)
        return None

    def find(self, query=None, *args, **kwargs):
        query = query or {}
        return FakeCursor([d for d in self.docs if self._matches(d, query)])

    async def update_one(self, query, update, upsert=False):
        for doc in self.docs:
            if self._matches(doc, query):
                if "$set" in update:
                    doc.update(update["$set"])
                return None
        if upsert:
            new_doc = dict(query)
            new_doc.update(update.get("$set", {}))
            self.docs.append(new_doc)
        return None

    async def insert_one(self, doc):
        self.docs.append(dict(doc))

    def _matches(self, doc, query):
        for key, expected in query.items():
            if key == "$or":
                if not any(self._matches(doc, sub) for sub in expected):
                    return False
                continue
            if isinstance(expected, dict):
                if "$in" in expected and doc.get(key) not in expected["$in"]:
                    return False
                continue
            if doc.get(key) != expected:
                return False
        return True


class FakeDatabase:
    def __init__(self, collections):
        self._collections = collections

    def __getitem__(self, name):
        return self._collections.setdefault(name, FakeCollection())


@pytest.fixture
def fake_db(monkeypatch):
    now = datetime.now(timezone.utc)
    db = FakeDatabase({
        "user_profiles": FakeCollection([
            {
                "_id": "user_alice",
                "name": "Alice",
                "email": "alice@example.com",
                "housing_type": "apartment",
                "has_children": False,
                "has_other_pets": False,
                "energy_budget": 3,
                "saved_pets": ["pet_dog_001"],
                "updated_at": now,
                "created_at": now,
            },
            {
                "_id": "user_bob",
                "name": "Bob",
                "email": "bob@example.com",
                "housing_type": "house_with_yard",
                "has_children": True,
                "has_other_pets": False,
                "energy_budget": 4,
                "saved_pets": [],
                "updated_at": now,
                "created_at": now,
            },
        ]),
        "notifications": FakeCollection([
            {
                "_id": "notif_alice_1",
                "recipient_role": "adopter",
                "recipient_id": "user_alice",
                "type": "application_update",
                "title": "Private alert for Alice",
                "message": "Alice only",
                "read": False,
                "created_at": now,
            },
        ]),
        "adoption_applications": FakeCollection([
            {
                "_id": "app_alice_1",
                "user_id": "user_alice",
                "pet_id": "pet_dog_001",
                "pet_name": "Buddy",
                "stage_status": "apply",
                "applicant_name": "Alice",
                "stage_history": [],
                "submitted_at": now,
                "updated_at": now,
            },
        ]),
        "pets": FakeCollection([
            {
                "_id": "pet_dog_001",
                "name": "Buddy",
                "species": "dog",
                "breed": "Golden Retriever",
                "age_months": 24,
                "gender": "Male",
                "size": "medium",
                "energy_level": 3,
                "good_with_kids": True,
                "good_with_other_pets": True,
                "housing_requirement": "apartment_or_house",
                "bio_text": "A friendly dog.",
                "status": "available",
            },
        ]),
    })

    for module in (users_router, notifications_router, adoptions_router):
        monkeypatch.setattr(module, "get_async_db", lambda: db, raising=False)
    return db


def bearer(user_id: str) -> dict:
    return {"Authorization": f"Bearer token_{user_id}"}


# ── Profile endpoints ────────────────────────────────────────────────

def test_profile_requires_credentials(fake_db):
    with TestClient(main.app) as client:
        assert client.get("/api/v1/users/user_alice/profile").status_code == 401


def test_profile_rejects_other_adopter(fake_db):
    with TestClient(main.app) as client:
        res = client.get("/api/v1/users/user_alice/profile", headers=bearer("user_bob"))
        assert res.status_code == 403


def test_profile_allows_owner(fake_db):
    with TestClient(main.app) as client:
        res = client.get("/api/v1/users/user_alice/profile", headers=bearer("user_alice"))
        assert res.status_code == 200
        assert res.json()["name"] == "Alice"


def test_profile_update_rejects_other_adopter(fake_db):
    with TestClient(main.app) as client:
        res = client.put(
            "/api/v1/users/user_alice/profile",
            headers=bearer("user_bob"),
            json={"energy_budget": 1},
        )
        assert res.status_code == 403


def test_saved_pets_rejects_other_adopter(fake_db):
    with TestClient(main.app) as client:
        res = client.get("/api/v1/users/user_alice/saved-pets", headers=bearer("user_bob"))
        assert res.status_code == 403


def test_favorite_rejects_other_adopter(fake_db):
    with TestClient(main.app) as client:
        res = client.post(
            "/api/v1/users/user_alice/favorite/pet_dog_001",
            headers=bearer("user_bob"),
        )
        assert res.status_code == 403


def test_shelter_jwt_cannot_use_adopter_endpoints(fake_db, monkeypatch):
    """A shelter token is not an adopter token and must be refused."""
    from app.services.auth import create_shelter_token

    token = create_shelter_token(shelter_id="shelter_x", email="x@org.in")
    with TestClient(main.app) as client:
        res = client.get(
            "/api/v1/users/user_alice/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 403


# ── Notification endpoints ───────────────────────────────────────────

def test_notifications_query_param_alone_is_rejected(fake_db):
    """The old ?user_id= bypass must be gone."""
    with TestClient(main.app) as client:
        res = client.get("/api/v1/notifications?user_id=user_alice")
        assert res.status_code == 401


def test_notifications_mismatched_query_param_is_forbidden(fake_db):
    with TestClient(main.app) as client:
        res = client.get(
            "/api/v1/notifications?user_id=user_alice",
            headers=bearer("user_bob"),
        )
        assert res.status_code == 403


def test_notifications_returns_only_own_records(fake_db):
    with TestClient(main.app) as client:
        own = client.get("/api/v1/notifications", headers=bearer("user_alice"))
        assert own.status_code == 200
        assert any("Alice only" in n["message"] for n in own.json())

        other = client.get("/api/v1/notifications", headers=bearer("user_bob"))
        assert other.status_code == 200
        assert other.json() == []


def test_unread_count_requires_credentials(fake_db):
    with TestClient(main.app) as client:
        assert client.get("/api/v1/notifications/unread-count").status_code == 401


# ── Adoption endpoints ───────────────────────────────────────────────

def test_application_status_rejects_other_adopter(fake_db):
    with TestClient(main.app) as client:
        res = client.get("/api/v1/adoptions/app_alice_1/status", headers=bearer("user_bob"))
        assert res.status_code == 403


def test_application_status_allows_owner(fake_db):
    with TestClient(main.app) as client:
        res = client.get("/api/v1/adoptions/app_alice_1/status", headers=bearer("user_alice"))
        assert res.status_code == 200
        assert res.json()["application_id"] == "app_alice_1"


def test_apply_rejects_impersonation(fake_db):
    with TestClient(main.app) as client:
        res = client.post(
            "/api/v1/adoptions/apply",
            headers=bearer("user_bob"),
            json={
                "user_id": "user_alice",
                "pet_id": "pet_dog_001",
                "applicant_name": "Bob",
                "applicant_email": "bob@example.com",
            },
        )
        assert res.status_code == 403


def test_apply_requires_credentials(fake_db):
    with TestClient(main.app) as client:
        res = client.post(
            "/api/v1/adoptions/apply",
            json={
                "user_id": "user_alice",
                "pet_id": "pet_dog_001",
                "applicant_name": "Alice",
                "applicant_email": "alice@example.com",
            },
        )
        assert res.status_code == 401


def test_user_pet_application_rejects_other_adopter(fake_db):
    with TestClient(main.app) as client:
        res = client.get(
            "/api/v1/adoptions/user/user_alice/pet/pet_dog_001",
            headers=bearer("user_bob"),
        )
        assert res.status_code == 403
