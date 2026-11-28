"""
Phase 2 tests:
- Shelter signup, login (bcrypt + signed JWT), profile GET/PUT
- Shelter ownership enforcement (401/403)
- Server-side age_group derivation
- Required matchable fields enforcement for status='available' vs 'draft'
- Embedding generation & failure fallback (embedding_pending=True, status='hidden', retry)
- Soft delete, photo upload, GET /pets status='available' + shelter enrichment
- Idempotent migrate_shelters script
"""

from copy import deepcopy
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app import main
from app.routers import pets as pets_router
from app.routers import shelters as shelters_router
from app.services import auth as auth_service
from app.scripts.migrate_shelters import migrate_shelters, DEFAULT_SHELTER_ID


class FakeAsyncCursor:
    def __init__(self, docs):
        self.docs = list(docs)

    def sort(self, key, direction):
        self.docs.sort(key=lambda d: d.get(key) or datetime.min.replace(tzinfo=timezone.utc), reverse=(direction < 0))
        return self

    def skip(self, n):
        self.docs = self.docs[n:]
        return self

    def limit(self, n):
        self.docs = self.docs[:n]
        return self

    async def to_list(self, length):
        return [deepcopy(d) for d in self.docs[:length]]


class FakeAsyncCollection:
    def __init__(self, initial=None):
        self.docs = [deepcopy(d) for d in (initial or [])]

    def _matches(self, doc, query):
        for k, v in query.items():
            if isinstance(v, dict):
                if "$in" in v and doc.get(k) not in v["$in"]:
                    return False
                if "$gt" in v:
                    val = doc.get(k)
                    if val is None or val <= v["$gt"]:
                        return False
            else:
                if doc.get(k) != v:
                    return False
        return True

    async def find_one(self, query, projection=None):
        for d in self.docs:
            if self._matches(d, query):
                return deepcopy(d)
        return None

    def find(self, query=None, projection=None):
        query = query or {}
        matched = [d for d in self.docs if self._matches(d, query)]
        return FakeAsyncCursor(matched)

    async def insert_one(self, doc):
        self.docs.append(deepcopy(doc))

    async def update_one(self, query, update, upsert=False):
        for idx, d in enumerate(self.docs):
            if self._matches(d, query):
                if "$set" in update:
                    self.docs[idx].update(deepcopy(update["$set"]))
                return
        if upsert and "$set" in update:
            new_doc = {**query, **deepcopy(update["$set"])}
            self.docs.append(new_doc)


class FakeSyncCollection:
    def __init__(self, initial=None):
        self.docs = [deepcopy(d) for d in (initial or [])]

    def find_one(self, query):
        for d in self.docs:
            if all(d.get(k) == v for k, v in query.items()):
                return deepcopy(d)
        return None

    def find(self, query=None):
        query = query or {}
        return [deepcopy(d) for d in self.docs if all(d.get(k) == v for k, v in query.items())]

    def insert_one(self, doc):
        self.docs.append(deepcopy(doc))

    def update_one(self, query, update):
        for idx, d in enumerate(self.docs):
            if all(d.get(k) == v for k, v in query.items()):
                if "$set" in update:
                    self.docs[idx].update(deepcopy(update["$set"]))
                return


class FakeDB:
    def __init__(self, collections):
        self.collections = collections

    def __getitem__(self, name):
        return self.collections[name]


def _setup_fake_env(monkeypatch):
    shelters_col = FakeAsyncCollection()
    pets_col = FakeAsyncCollection()
    db = FakeDB({"shelters": shelters_col, "pets": pets_col})

    monkeypatch.setattr(shelters_router, "get_async_db", lambda: db)
    monkeypatch.setattr(pets_router, "get_async_db", lambda: db)
    monkeypatch.setattr(auth_service, "get_async_db", lambda: db)
    monkeypatch.setattr(main, "setup_standard_indexes", lambda: {})
    monkeypatch.setattr(main, "setup_atlas_vector_search_index", lambda: True)
    monkeypatch.setattr(main, "close_clients", lambda: None)

    async def _fake_embed(pet_doc):
        return [0.1] * 768, False

    monkeypatch.setattr(shelters_router, "generate_pet_embedding_async", _fake_embed)
    return db, shelters_col, pets_col


def _valid_pet_payload(**overrides):
    base = {
        "name": "Mochi",
        "species": "dog",
        "breed": "Beagle",
        "age_months": 18,
        "gender": "Female",
        "size": "medium",
        "energy_level": 3,
        "grooming_needs": "low",
        "shedding_level": "moderate",
        "noise_level": "moderate",
        "alone_time_tolerance": "moderate",
        "experience_level_required": "first_time_friendly",
        "good_with_kids": True,
        "good_with_other_pets": True,
        "housing_requirement": "apartment_or_house",
        "hypoallergenic": False,
        "bio_text": "Mochi is a gentle, curious beagle who loves afternoon walks and naps.",
        "temperament": ["Gentle", "Curious"],
        "status": "available",
    }
    base.update(overrides)
    return base


def _signup_shelter(client: TestClient, name: str, email: str, password: str = "Secret123!"):
    return client.post("/api/v1/shelters/auth/signup", json={
        "name": name,
        "email": email,
        "password": password,
        "contact_phone": "+91-9876543210",
        "address": "42 Rescue Lane",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
    })


def test_shelter_signup_login_and_profile(monkeypatch):
    _setup_fake_env(monkeypatch)
    with TestClient(main.app) as client:
        res = _signup_shelter(client, "Happy Paws", "hello@happypaws.org")
        assert res.status_code == 201
        body = res.json()
        assert body["role"] == "shelter"
        assert body["token"]
        assert body["shelter"]["email"] == "hello@happypaws.org"
        assert "password_hash" not in body["shelter"]

        # Duplicate email rejected
        dup = _signup_shelter(client, "Happy Paws 2", "hello@happypaws.org")
        assert dup.status_code == 409

        # Wrong password rejected
        bad_login = client.post("/api/v1/shelters/auth/login", json={
            "email": "hello@happypaws.org",
            "password": "WrongPassword",
        })
        assert bad_login.status_code == 401

        # Correct login succeeds
        good_login = client.post("/api/v1/shelters/auth/login", json={
            "email": "hello@happypaws.org",
            "password": "Secret123!",
        })
        assert good_login.status_code == 200
        token = good_login.json()["token"]

        # Profile GET & PUT
        me = client.get("/api/v1/shelters/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["name"] == "Happy Paws"

        upd = client.put(
            "/api/v1/shelters/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"city": "Pune", "operating_hours": "9am-5pm"},
        )
        assert upd.status_code == 200
        assert upd.json()["city"] == "Pune"
        assert upd.json()["operating_hours"] == "9am-5pm"


def test_shelter_pet_ownership_enforcement(monkeypatch):
    _setup_fake_env(monkeypatch)
    with TestClient(main.app) as client:
        # Unauthenticated request rejected
        unauth = client.get("/api/v1/shelters/me/pets")
        assert unauth.status_code == 401

        token_a = _signup_shelter(client, "Shelter A", "a@shelter.org").json()["token"]
        token_b = _signup_shelter(client, "Shelter B", "b@shelter.org").json()["token"]

        # Shelter A creates a pet
        created = client.post(
            "/api/v1/shelters/me/pets",
            headers={"Authorization": f"Bearer {token_a}"},
            json=_valid_pet_payload(),
        )
        assert created.status_code == 201
        pet_id = created.json()["_id"]

        # Shelter B cannot read, update, status-change, or delete Shelter A's pet
        assert client.get(f"/api/v1/shelters/me/pets/{pet_id}", headers={"Authorization": f"Bearer {token_b}"}).status_code == 403
        assert client.put(f"/api/v1/shelters/me/pets/{pet_id}", headers={"Authorization": f"Bearer {token_b}"}, json={"name": "Hacked"}).status_code == 403
        assert client.patch(f"/api/v1/shelters/me/pets/{pet_id}/status", headers={"Authorization": f"Bearer {token_b}"}, json={"status": "hidden"}).status_code == 403
        assert client.delete(f"/api/v1/shelters/me/pets/{pet_id}", headers={"Authorization": f"Bearer {token_b}"}).status_code == 403


def test_age_group_derived_server_side_and_required_fields_enforced(monkeypatch):
    _setup_fake_env(monkeypatch)
    with TestClient(main.app) as client:
        token = _signup_shelter(client, "Shelter A", "a@shelter.org").json()["token"]

        # Incomplete payload rejected for status='available'
        incomplete = _valid_pet_payload()
        del incomplete["grooming_needs"]
        bad = client.post(
            "/api/v1/shelters/me/pets",
            headers={"Authorization": f"Bearer {token}"},
            json=incomplete,
        )
        assert bad.status_code == 422

        # Short bio rejected for status='available'
        short_bio = _valid_pet_payload(bio_text="Too short")
        bad_bio = client.post(
            "/api/v1/shelters/me/pets",
            headers={"Authorization": f"Bearer {token}"},
            json=short_bio,
        )
        assert bad_bio.status_code == 422

        # Incomplete payload allowed for status='draft'
        incomplete["status"] = "draft"
        draft = client.post(
            "/api/v1/shelters/me/pets",
            headers={"Authorization": f"Bearer {token}"},
            json=incomplete,
        )
        assert draft.status_code == 201
        assert draft.json()["status"] == "draft"

        # Server computes age_group from age_months, ignoring any client-supplied value
        payload = _valid_pet_payload(age_months=90)
        payload["age_group"] = "puppy_or_kitten"  # client tries to spoof
        created = client.post(
            "/api/v1/shelters/me/pets",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
        assert created.status_code == 201
        assert created.json()["age_group"] == "senior"


def test_embedding_failure_hides_pet_and_retry_recovers(monkeypatch):
    db, _, pets_col = _setup_fake_env(monkeypatch)

    async def _failing_embed(pet_doc):
        return None, True

    monkeypatch.setattr(shelters_router, "generate_pet_embedding_async", _failing_embed)

    with TestClient(main.app) as client:
        token = _signup_shelter(client, "Shelter A", "a@shelter.org").json()["token"]
        created = client.post(
            "/api/v1/shelters/me/pets",
            headers={"Authorization": f"Bearer {token}"},
            json=_valid_pet_payload(),
        )
        assert created.status_code == 201
        pet = created.json()
        assert pet["embedding_pending"] is True
        assert pet["status"] == "hidden"

        # Hidden pet is NOT visible in public GET /pets
        public_list = client.get("/api/v1/pets")
        assert public_list.status_code == 200
        assert public_list.json() == []

        # Retry succeeds and restores status='available'
        async def _working_embed(pet_doc):
            return [0.2] * 768, False

        monkeypatch.setattr(shelters_router, "generate_pet_embedding_async", _working_embed)
        retried = client.post(
            f"/api/v1/shelters/me/pets/{pet['_id']}/retry-embedding",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert retried.status_code == 200
        assert retried.json()["embedding_pending"] is False
        assert retried.json()["status"] == "available"

        # Now visible in public GET /pets with shelter_name & shelter_city
        public_list_after = client.get("/api/v1/pets")
        assert len(public_list_after.json()) == 1
        item = public_list_after.json()[0]
        assert item["shelter_name"] == "Shelter A"
        assert item["shelter_city"] == "Bengaluru"
        assert "embedding" not in item

        # Soft delete hides it again without deleting from DB
        deleted = client.delete(
            f"/api/v1/shelters/me/pets/{pet['_id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert deleted.status_code == 200
        assert deleted.json()["status"] == "hidden"
        assert len(pets_col.docs) == 1
        assert client.get(f"/api/v1/pets/{pet['_id']}").status_code == 404


def test_migrate_shelters_is_idempotent():
    shelters_col = FakeSyncCollection()
    pets_col = FakeSyncCollection([
        {
            "_id": "pet_dog_001",
            "name": "Buddy",
            "species": "dog",
            "age_months": 24,
            "shedding_level": "low",
            "temperament": ["Friendly"],
            "bio_text": "Sweet dog.",
            "embedding": [0.1] * 768,
        }
    ])
    fake_db = FakeDB({"shelters": shelters_col, "pets": pets_col})

    first = migrate_shelters(fake_db)
    assert first["created_default_shelter"] == 1
    assert first["updated_pets"] == 1
    assert len(shelters_col.docs) == 1
    assert pets_col.docs[0]["shelter_id"] == DEFAULT_SHELTER_ID
    assert pets_col.docs[0]["status"] == "available"
    assert pets_col.docs[0]["hypoallergenic"] is True
    assert pets_col.docs[0]["age_group"] == "young"

    # Second run does not duplicate or overwrite
    second = migrate_shelters(fake_db)
    assert second["created_default_shelter"] == 0
    assert second["updated_pets"] == 0
    assert len(shelters_col.docs) == 1
