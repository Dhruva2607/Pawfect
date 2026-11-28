"""
Phase 3 tests:
- Application submission copies shelter_id, snapshots lifestyle, computes compatibility_score
- Notification delivered ONLY to the owning shelter, naming pet and applicant
- Shelter application list/detail ownership (403 for other shelter)
- Stage transitions (apply -> review -> adopt / rejected; invalid transitions -> 422)
- Adopt side effects: pet becomes 'adopted', other open applications auto-declined + notified
- Shelter stats & notification read/unread endpoints
"""

from copy import deepcopy
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app import main
from app.models.pet import Pet
from app.routers import adoptions as adoptions_router
from app.routers import notifications as notifications_router
from app.routers import shelters as shelters_router
from app.services import auth as auth_service
from app.services.nodes import SinglePetCompatibility


def adopter_headers(user_id: str) -> dict:
    """Authorization header for a demo adopter token."""
    return {"Authorization": f"Bearer token_{user_id}"}


class FakeCursor:
    def __init__(self, docs):
        self.docs = list(docs)

    def sort(self, key, direction):
        self.docs.sort(
            key=lambda d: d.get(key) or datetime.min.replace(tzinfo=timezone.utc),
            reverse=(direction < 0),
        )
        return self

    def skip(self, n):
        self.docs = self.docs[n:]
        return self

    def limit(self, n):
        self.docs = self.docs[:n]
        return self

    async def to_list(self, length):
        return [deepcopy(d) for d in self.docs[:length]]


class FakeCollection:
    def __init__(self, initial=None):
        self.docs = [deepcopy(d) for d in (initial or [])]

    def _matches(self, doc, query):
        for k, v in query.items():
            if isinstance(v, dict):
                if "$in" in v and doc.get(k) not in v["$in"]:
                    return False
                if "$ne" in v and doc.get(k) == v["$ne"]:
                    return False
            else:
                if doc.get(k) != v:
                    return False
        return True

    async def find_one(self, query, projection=None, sort=None):
        matches = [d for d in self.docs if self._matches(d, query)]
        if sort and matches:
            key, direction = sort[0]
            matches.sort(
                key=lambda d: d.get(key) or datetime.min.replace(tzinfo=timezone.utc),
                reverse=(direction < 0),
            )
        return deepcopy(matches[0]) if matches else None

    def find(self, query=None, projection=None):
        query = query or {}
        return FakeCursor([d for d in self.docs if self._matches(d, query)])

    async def count_documents(self, query):
        return sum(1 for d in self.docs if self._matches(d, query))

    async def insert_one(self, doc):
        self.docs.append(deepcopy(doc))

    async def update_one(self, query, update, upsert=False):
        for idx, d in enumerate(self.docs):
            if self._matches(d, query):
                if "$set" in update:
                    self.docs[idx].update(deepcopy(update["$set"]))
                return

    async def update_many(self, query, update):
        for idx, d in enumerate(self.docs):
            if self._matches(d, query):
                if "$set" in update:
                    self.docs[idx].update(deepcopy(update["$set"]))


class FakeDB:
    def __init__(self, cols):
        self.cols = cols

    def __getitem__(self, name):
        return self.cols[name]


def _setup(monkeypatch):
    shelters_col = FakeCollection()
    pets_col = FakeCollection()
    users_col = FakeCollection([
        {
            "_id": "user_priya",
            "name": "Priya Sharma",
            "email": "priya@example.com",
            "housing_type": "apartment",
            "has_children": False,
            "has_other_pets": False,
            "energy_budget": 3,
        },
        {
            "_id": "user_arjun",
            "name": "Arjun Mehta",
            "email": "arjun@example.com",
            "housing_type": "house_with_yard",
            "has_children": True,
            "has_other_pets": False,
            "energy_budget": 4,
        },
    ])
    sessions_col = FakeCollection([
        {
            "_id": "sess_1",
            "user_id": "user_priya",
            "extracted_constraints": {"preferred_size": "medium", "daily_alone_hours": 4},
            "updated_at": datetime.now(timezone.utc),
        }
    ])
    apps_col = FakeCollection()
    notifs_col = FakeCollection()

    db = FakeDB({
        "shelters": shelters_col,
        "pets": pets_col,
        "user_profiles": users_col,
        "user_sessions": sessions_col,
        "adoption_applications": apps_col,
        "notifications": notifs_col,
    })

    for mod in (shelters_router, adoptions_router, notifications_router, auth_service):
        monkeypatch.setattr(mod, "get_async_db", lambda: db)

    monkeypatch.setattr(main, "setup_standard_indexes", lambda: {})
    monkeypatch.setattr(main, "setup_atlas_vector_search_index", lambda: True)
    monkeypatch.setattr(main, "close_clients", lambda: None)

    async def _fake_embed(pet_doc):
        return [0.1] * 768, False

    monkeypatch.setattr(shelters_router, "generate_pet_embedding_async", _fake_embed)

    async def _fake_eval(pet: Pet, lifestyle, use_llm=True):
        return SinglePetCompatibility(
            pet_id=pet.id,
            pet_name=pet.name,
            compatibility_score=91,
            pros=["Matches apartment"],
            caveats=["Moderate daily walks"],
            reasoning_summary=f"{pet.name} is a great 91% match.",
        )

    monkeypatch.setattr(adoptions_router, "evaluate_pet_compatibility", _fake_eval)
    return db, shelters_col, pets_col, apps_col, notifs_col


def _create_shelter_and_pet(client: TestClient, name: str, email: str, pet_name: str):
    s = client.post("/api/v1/shelters/auth/signup", json={
        "name": name,
        "email": email,
        "password": "Password123!",
        "contact_phone": "+91-9000000000",
        "address": "10 Main St",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
    }).json()
    token = s["token"]
    shelter_id = s["shelter"]["_id"]
    pet = client.post(
        "/api/v1/shelters/me/pets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": pet_name,
            "species": "dog",
            "breed": "Indie",
            "age_months": 20,
            "gender": "Female",
            "size": "medium",
            "energy_level": 3,
            "grooming_needs": "low",
            "shedding_level": "low",
            "noise_level": "quiet",
            "alone_time_tolerance": "moderate",
            "experience_level_required": "first_time_friendly",
            "good_with_kids": True,
            "good_with_other_pets": True,
            "housing_requirement": "apartment_or_house",
            "hypoallergenic": True,
            "bio_text": "Gentle, affectionate companion who loves morning walks and belly rubs.",
            "status": "available",
        },
    ).json()
    return token, shelter_id, pet["_id"]


def test_apply_notifies_owning_shelter_only_and_computes_compatibility(monkeypatch):
    _, _, _, apps_col, notifs_col = _setup(monkeypatch)
    with TestClient(main.app) as client:
        token_a, shelter_a, pet_a = _create_shelter_and_pet(client, "Shelter A", "a@org.in", "Mochi")
        token_b, shelter_b, _ = _create_shelter_and_pet(client, "Shelter B", "b@org.in", "Rocky")

        res = client.post("/api/v1/adoptions/apply", headers=adopter_headers("user_priya"), json={
            "user_id": "user_priya",
            "pet_id": pet_a,
            "applicant_name": "Priya Sharma",
            "applicant_email": "priya@example.com",
            "notes": "Work from home most days.",
        })
        assert res.status_code == 201
        body = res.json()
        assert body["shelter_id"] == shelter_a
        assert body["compatibility_score"] == 91
        assert len(body["stage_history"]) == 1
        assert body["stage_history"][0]["stage"] == "apply"

        # Lifestyle snapshot stored on application
        stored_app = apps_col.docs[0]
        assert stored_app["applicant_lifestyle"]["housing_type"] == "apartment"
        assert stored_app["applicant_lifestyle"]["daily_alone_hours"] == 4

        # Shelter A received notification naming pet and applicant; Shelter B did NOT
        notifs_a = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {token_a}"}).json()
        notifs_b = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {token_b}"}).json()
        assert len(notifs_a) == 1
        assert "Mochi" in notifs_a[0]["message"]
        assert "Priya Sharma" in notifs_a[0]["message"]
        assert notifs_b == []

        # Unread count & mark read
        assert client.get("/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {token_a}"}).json()["unread_count"] == 1
        client.patch(f"/api/v1/notifications/{notifs_a[0]['_id']}/read", headers={"Authorization": f"Bearer {token_a}"})
        assert client.get("/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {token_a}"}).json()["unread_count"] == 0


def test_stage_transitions_and_adopt_auto_declines_other_applicants(monkeypatch):
    _, _, pets_col, _, _ = _setup(monkeypatch)
    with TestClient(main.app) as client:
        token_a, _, pet_a = _create_shelter_and_pet(client, "Shelter A", "a@org.in", "Mochi")
        token_b, _, _ = _create_shelter_and_pet(client, "Shelter B", "b@org.in", "Rocky")

        app1 = client.post("/api/v1/adoptions/apply", headers=adopter_headers("user_priya"), json={
            "user_id": "user_priya",
            "pet_id": pet_a,
            "applicant_name": "Priya Sharma",
            "applicant_email": "priya@example.com",
        }).json()["application_id"]

        app2 = client.post("/api/v1/adoptions/apply", headers=adopter_headers("user_arjun"), json={
            "user_id": "user_arjun",
            "pet_id": pet_a,
            "applicant_name": "Arjun Mehta",
            "applicant_email": "arjun@example.com",
        }).json()["application_id"]

        # Shelter B cannot view or modify Shelter A's application
        assert client.get(f"/api/v1/shelters/me/applications/{app1}", headers={"Authorization": f"Bearer {token_b}"}).status_code == 403
        assert client.patch(
            f"/api/v1/shelters/me/applications/{app1}/stage",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"stage_status": "review"},
        ).status_code == 403

        # Invalid direct jump apply -> adopt rejected
        bad_jump = client.patch(
            f"/api/v1/shelters/me/applications/{app1}/stage",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"stage_status": "adopt"},
        )
        assert bad_jump.status_code == 422

        # Valid: apply -> review
        rev = client.patch(
            f"/api/v1/shelters/me/applications/{app1}/stage",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"stage_status": "review", "shelter_note": "Meet & greet scheduled for Saturday"},
        )
        assert rev.status_code == 200
        assert rev.json()["stage_status"] == "review"
        assert rev.json()["shelter_note"] == "Meet & greet scheduled for Saturday"

        # Valid: review -> adopt
        adopted = client.patch(
            f"/api/v1/shelters/me/applications/{app1}/stage",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"stage_status": "adopt", "shelter_note": "Welcome home!"},
        )
        assert adopted.status_code == 200
        assert adopted.json()["stage_status"] == "adopt"

        # Pet is now adopted
        pet_doc = next(p for p in pets_col.docs if p["_id"] == pet_a)
        assert pet_doc["status"] == "adopted"

        # Arjun's competing application was auto-declined to 'rejected'
        arjun_status = client.get(
            f"/api/v1/adoptions/{app2}/status", headers=adopter_headers("user_arjun")
        ).json()
        assert arjun_status["stage_status"] == "rejected"

        # Arjun received an auto-decline notification
        arjun_notifs = client.get(
            "/api/v1/notifications", headers=adopter_headers("user_arjun")
        ).json()
        assert any(n["type"] == "application_auto_declined" for n in arjun_notifs)

        # Stats reflect adopted pet & applications
        stats = client.get("/api/v1/shelters/me/stats", headers={"Authorization": f"Bearer {token_a}"}).json()
        assert stats["adopted_pets"] == 1
        assert stats["adopted_applications"] == 1
        assert stats["rejected_applications"] == 1
        assert stats["available_pets"] == 0
