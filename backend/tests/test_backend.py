import asyncio
import json

import pytest
from fastapi.testclient import TestClient
from pymongo.errors import OperationFailure

from app import main
from app.database import indexes
from app.routers import chat, matches
from app.routers import pets as pets_router
from app.routers.matches import DirectEvalRequest
from app.services import retrieval
from app.services.nodes import SinglePetCompatibility


class EmptyPetsCollection:
    def __init__(self):
        self.find_queries = []
        self.aggregate_calls = 0

    def aggregate(self, pipeline):
        self.aggregate_calls += 1
        raise OperationFailure("Vector search is unavailable", 8000)

    def find(self, query):
        self.find_queries.append(query)
        return []


class FakeDatabase:
    def __init__(self, collections):
        self.collections = collections

    def __getitem__(self, name):
        return self.collections[name]


def prepare_test_app(monkeypatch):
    monkeypatch.setattr(main, "setup_standard_indexes", lambda: {})
    monkeypatch.setattr(main, "setup_atlas_vector_search_index", lambda: True)
    monkeypatch.setattr(main, "close_clients", lambda: None)


def test_cosine_similarity_handles_mismatched_and_zero_vectors():
    assert retrieval.compute_cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert retrieval.compute_cosine_similarity([1.0], [1.0, 2.0]) == 0.0
    assert retrieval.compute_cosine_similarity([0.0], [1.0]) == 0.0


def test_allergy_prefilter_requires_documented_low_shedding_traits():
    query = retrieval.build_mql_prefilter({
        "species": "dog",
        "has_children": True,
        "has_other_pets": True,
        "housing_type": "apartment",
        "allergies": True,
    })

    assert query["species"] == "dog"
    assert query["good_with_kids"] is True
    assert query["good_with_other_pets"] is True
    assert query["housing_requirement"] == {"$in": ["apartment", "apartment_or_house"]}
    assert "$or" in query


def test_existing_vector_index_is_updated_when_its_filter_fields_are_stale():
    class SearchIndexCollection:
        def __init__(self):
            self.updated = None

        def list_search_indexes(self):
            return [{
                "name": indexes.ATLAS_VECTOR_SEARCH_INDEX_NAME,
                "latestDefinition": {"fields": []},
            }]

        def update_search_index(self, name, definition):
            self.updated = (name, definition)

    collection = SearchIndexCollection()

    result = indexes.setup_atlas_vector_search_index(
        FakeDatabase({"pets": collection})
    )

    assert result is True
    assert collection.updated == (
        indexes.ATLAS_VECTOR_SEARCH_INDEX_NAME,
        indexes.ATLAS_VECTOR_SEARCH_INDEX_DEFINITION["definition"],
    )


def test_retrieval_never_drops_required_constraints_when_no_candidates(monkeypatch):
    collection = EmptyPetsCollection()
    monkeypatch.setattr(retrieval, "generate_embedding", lambda _: [1.0] * 768)

    result = retrieval.hybrid_search_pets(
        query_text="family dog",
        constraints={"species": "dog", "has_children": True},
        db=FakeDatabase({"pets": collection}),
    )

    assert result == []
    assert collection.find_queries == [{"species": "dog", "good_with_kids": True}]


def test_allergy_search_skips_vector_filter_and_keeps_all_constraints(monkeypatch):
    collection = EmptyPetsCollection()
    monkeypatch.setattr(retrieval, "generate_embedding", lambda _: [1.0] * 768)
    constraints = {"species": "dog", "allergies": True}
    expected_query = retrieval.build_mql_prefilter(constraints)

    result = retrieval.hybrid_search_pets(
        query_text="low shedding dog",
        constraints=constraints,
        db=FakeDatabase({"pets": collection}),
    )

    assert result == []
    assert collection.aggregate_calls == 0
    assert collection.find_queries == [expected_query]


def test_health_reports_mongodb_unavailable(monkeypatch):
    class UnavailableDatabase:
        async def command(self, command):
            raise ConnectionError("MongoDB is unavailable")

    monkeypatch.setattr(main, "get_async_db", lambda: UnavailableDatabase())

    response = asyncio.run(main.health_check())

    assert response.status_code == 503
    assert json.loads(response.body)["database"] == "unavailable"


def test_liveness_does_not_depend_on_mongodb():
    response = asyncio.run(main.liveness_check())

    assert response["status"] == "alive"


def test_http_health_routes_and_pet_catalog(monkeypatch):
    class HealthyDatabase:
        available = True

        async def command(self, command):
            if not self.available:
                raise ConnectionError("MongoDB is unavailable")
            return {"ok": 1}

    class PetCursor:
        def limit(self, limit):
            return self

        async def to_list(self, length):
            return [{
                "_id": "pet-1",
                "name": "Buddy",
                "species": "dog",
                "breed": "Mixed breed",
                "age_months": 24,
                "gender": "Male",
                "size": "medium",
                "energy_level": 3,
                "good_with_kids": True,
                "good_with_other_pets": True,
                "temperament": [],
                "housing_requirement": "apartment",
                "bio_text": "Friendly and calm.",
                "embedding": [0.5] * 768,
            }]

    class PetsCollection:
        def __init__(self):
            self.query = None

        def find(self, query):
            self.query = query
            return PetCursor()

    collection = PetsCollection()
    database = HealthyDatabase()
    monkeypatch.setattr(main, "get_async_db", lambda: database)
    monkeypatch.setattr(
        pets_router,
        "get_async_db",
        lambda: FakeDatabase({"pets": collection}),
    )
    prepare_test_app(monkeypatch)

    with TestClient(main.app) as client:
        health = client.get("/health")
        liveness = client.get("/health/live")
        pets = client.get("/api/v1/pets?species=DOG")
        database.available = False
        unavailable = client.get("/health")

    assert health.status_code == 200
    assert health.json()["database"] == "connected"
    assert liveness.status_code == 200
    assert liveness.json()["status"] == "alive"
    assert pets.status_code == 200
    assert pets.json()[0]["_id"] == "pet-1"
    assert "embedding" not in pets.json()[0]
    assert collection.query == {"species": "dog"}
    assert unavailable.status_code == 503
    assert unavailable.json()["database"] == "unavailable"


def test_direct_evaluation_fallback_is_persisted(monkeypatch):
    class PetsCollection:
        async def find_one(self, query):
            return {
                "_id": "pet-1",
                "name": "Buddy",
                "species": "dog",
                "breed": "Mixed breed",
                "age_months": 24,
                "gender": "Male",
                "size": "medium",
                "energy_level": 3,
                "good_with_kids": True,
                "good_with_other_pets": True,
                "temperament": [],
                "housing_requirement": "apartment",
                "bio_text": "Friendly and calm.",
            }

    class EvaluationsCollection:
        def __init__(self):
            self.upserts = []

        async def update_one(self, query, update, upsert=False):
            self.upserts.append((query, update, upsert))

    evaluations = EvaluationsCollection()
    db = FakeDatabase({"pets": PetsCollection(), "match_evaluations": evaluations})
    monkeypatch.setattr(matches, "get_async_db", lambda: db)

    class FailingLLM:
        def with_structured_output(self, _):
            return self

        async def ainvoke(self, _):
            raise RuntimeError("LLM unavailable")

    monkeypatch.setattr(matches, "get_chat_llm", lambda **_: FailingLLM())
    response = asyncio.run(matches.direct_eval(
        DirectEvalRequest(session_id="session-1", pet_id="pet-1")
    ))

    assert response.pet_id == "pet-1"
    assert len(evaluations.upserts) == 1
    query, update, upsert = evaluations.upserts[0]
    assert query == {"session_id": "session-1", "pet_id": "pet-1"}
    assert upsert is True
    assert update["$set"]["pet_id"] == "pet-1"
    assert "_id" not in update["$set"]


def test_direct_evaluation_does_not_mask_persistence_failure(monkeypatch):
    class PetsCollection:
        async def find_one(self, query):
            return {
                "_id": "pet-1",
                "name": "Buddy",
                "species": "dog",
                "breed": "Mixed breed",
                "age_months": 24,
                "gender": "Male",
                "size": "medium",
                "energy_level": 3,
                "good_with_kids": True,
                "good_with_other_pets": True,
                "temperament": [],
                "housing_requirement": "apartment",
                "bio_text": "Friendly and calm.",
            }

    class FailingEvaluationsCollection:
        async def update_one(self, query, update, upsert=False):
            raise RuntimeError("Evaluation persistence failed")

    db = FakeDatabase({
        "pets": PetsCollection(),
        "match_evaluations": FailingEvaluationsCollection(),
    })
    monkeypatch.setattr(matches, "get_async_db", lambda: db)

    class SuccessfulLLM:
        def with_structured_output(self, _):
            return self

        async def ainvoke(self, _):
            return SinglePetCompatibility(
                pet_id="pet-1",
                pet_name="Buddy",
                compatibility_score=90,
                pros=["Calm temperament"],
                caveats=["Daily exercise needed"],
                reasoning_summary="A good fit.",
            )

    monkeypatch.setattr(matches, "get_chat_llm", lambda **_: SuccessfulLLM())

    with pytest.raises(RuntimeError, match="Evaluation persistence failed"):
        asyncio.run(matches.direct_eval(
            DirectEvalRequest(session_id="session-1", pet_id="pet-1")
        ))


def test_sse_reports_chat_persistence_failures(monkeypatch):
    monkeypatch.setattr(chat, "run_matchmaker_turn", lambda *args: {
        "response_message": "Hello!",
        "quick_replies": [],
        "is_complete": False,
        "candidate_matches": [],
        "evaluations": [],
        "extracted_constraints": {},
    })

    async def fail_to_save(**kwargs):
        raise RuntimeError("MongoDB is unavailable")

    monkeypatch.setattr(chat, "_save_session_data", fail_to_save)

    async def collect_events():
        return [
            event async for event in chat._generate_sse_stream(
                "session-1", None, "Hello", [], {}
            )
        ]

    events = asyncio.run(collect_events())

    assert events[-1]["event"] == "error"
    assert json.loads(events[-1]["data"])["event"] == "error"
    assert all(event["event"] != "done" for event in events)


def test_conversational_intake_rejects_irrelevant_or_unsupported_species(monkeypatch):
    from app.services import nodes
    from app.services.nodes import IntakeAnalysisOutput
    from app.services.state import LifestyleConstraints

    class FakeStructuredLLM:
        def invoke(self, messages):
            return IntakeAnalysisOutput(
                extracted_constraints=LifestyleConstraints(),
                is_sufficient_for_search=False,
                is_unsupported_or_irrelevant=True,
                follow_up_question="We are only an adoption center for cats and dogs. Would you like to adopt a dog or cat?",
                suggested_quick_replies=["Looking for a Dog", "Looking for a Cat"]
            )

    class FakeLLM:
        def with_structured_output(self, schema):
            return FakeStructuredLLM()

    monkeypatch.setattr(nodes, "get_chat_llm", lambda **_: FakeLLM())

    state = {
        "user_message": "Do you have parrots or reptiles?",
        "conversation_history": [],
        "extracted_constraints": {},
    }
    result = nodes.conversational_intake_node(state)

    assert result["is_complete"] is False
    assert "cat" in result["response_message"].lower()
    assert "dog" in result["response_message"].lower()
    assert "Looking for a Dog" in result["quick_replies"]


def test_reasoning_scoring_includes_comparison_to_hero(monkeypatch):
    from app.services import nodes

    class FakeScoringLLM:
        def invoke(self, messages):
            raise RuntimeError("Force fallback to test grounded deterministic scoring")

    class FakeLLM:
        def with_structured_output(self, schema):
            return FakeScoringLLM()

    monkeypatch.setattr(nodes, "get_chat_llm", lambda **_: FakeLLM())

    state = {
        "extracted_constraints": {"housing_type": "apartment", "energy_budget": 3},
        "candidate_matches": [
            {
                "_id": "pet-1",
                "name": "Luna",
                "species": "dog",
                "breed": "Poodle",
                "score": 0.95,
                "housing_requirement": "apartment",
                "temperament": ["calm", "gentle"],
                "exercise_needs": "30 mins daily"
            },
            {
                "_id": "pet-2",
                "name": "Thor",
                "species": "dog",
                "breed": "Husky",
                "score": 0.75,
                "housing_requirement": "house_with_yard",
                "temperament": ["energetic"],
                "exercise_needs": "90 mins high-intensity running"
            }
        ]
    }

    result = nodes.reasoning_scoring_node(state)
    evals = result["evaluations"]
    assert len(evals) == 2
    # Hero pet
    assert evals[0]["pet_name"] == "Luna"
    assert evals[0]["comparison_to_hero"] is None
    # Alternative match
    assert evals[1]["pet_name"] == "Thor"
    assert evals[1]["comparison_to_hero"] is not None
    assert "Luna" in evals[1]["comparison_to_hero"]
    # Overall response mentions alternative matches compared to hero pet
    assert "Thor" in result["response_message"]


def test_adoption_duplicate_submission_rejected(monkeypatch):
    from fastapi import HTTPException
    from app.routers import adoptions
    from app.routers.adoptions import AdoptionApplyRequest

    applications_db = {}

    class FakeAdoptionCollection:
        async def find_one(self, query):
            if "user_id" in query and "pet_id" in query:
                key = (query["user_id"], query["pet_id"])
                return applications_db.get(key)
            return None

        async def insert_one(self, doc):
            key = (doc["user_id"], doc["pet_id"])
            applications_db[key] = doc

    class FakeUserCollection:
        async def find_one(self, query):
            return {"_id": query["_id"], "name": "Adopter", "email": "test@test.com"}

    class FakePetCollection:
        async def find_one(self, query):
            return {
                "_id": query["_id"],
                "name": "Buddy",
                "species": "dog",
                "breed": "Golden",
                "age_months": 24,
                "gender": "Male",
                "size": "medium",
                "energy_level": 3,
                "good_with_kids": True,
                "good_with_other_pets": True,
                "housing_requirement": "apartment",
                "bio_text": "Good dog"
            }

    fake_db = FakeDatabase({
        "adoption_applications": FakeAdoptionCollection(),
        "user_profiles": FakeUserCollection(),
        "pets": FakePetCollection()
    })
    monkeypatch.setattr(adoptions, "get_async_db", lambda: fake_db)

    req = AdoptionApplyRequest(
        user_id="user_123",
        pet_id="pet_dog_001",
        applicant_name="John Doe",
        applicant_email="john@example.com"
    )

    # 1. First submission should succeed
    first_res = asyncio.run(adoptions.apply_adoption(req))
    assert first_res.applicant_name == "John Doe"
    assert first_res.pet_id == "pet_dog_001"

    # 2. Second submission for same user and pet MUST be rejected with HTTP 409
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(adoptions.apply_adoption(req))
    assert excinfo.value.status_code == 409
    assert "already submitted" in excinfo.value.detail.lower()

    # 3. Check endpoint returns existing application
    check_res = asyncio.run(adoptions.get_user_pet_application("user_123", "pet_dog_001"))
    assert check_res is not None
    assert check_res.application_id == first_res.application_id

    # 4. Check endpoint returns None for unapplied pet
    none_res = asyncio.run(adoptions.get_user_pet_application("user_123", "pet_dog_999"))
    assert none_res is None


def test_seed_pets_contain_rich_attributes_and_validate():
    from app.models.pet import Pet
    from app.scripts.seed_pets import RAW_PET_RECORDS, create_pet_embedding_text

    assert len(RAW_PET_RECORDS) >= 36
    for record in RAW_PET_RECORDS:
        pet = Pet(**record)
        assert pet.age_group in {"puppy_or_kitten", "young", "adult", "senior"}
        assert pet.weight_lbs is not None and pet.weight_lbs > 0
        assert pet.grooming_needs in {"low", "moderate", "high"}
        assert pet.shedding_level in {"low", "moderate", "high"}
        assert pet.noise_level in {"quiet", "moderate", "vocal"}
        assert pet.alone_time_tolerance in {"low", "moderate", "high"}
        assert pet.experience_level_required in {"first_time_friendly", "experienced_preferred"}
        assert pet.training_level in {"basic", "house_trained", "well_trained"}
        assert pet.coat_type in {"short", "medium", "long", "curly_hypoallergenic"}

        emb_text = create_pet_embedding_text(record)
        assert "Grooming needs:" in emb_text
        assert "Noise level:" in emb_text


def test_mql_prefilter_applies_signup_and_chatbot_constraints():
    query = retrieval.build_mql_prefilter({
        "housing_type": "apartment",
        "has_children": True,
        "has_other_pets": False,
        "energy_budget": 2,
        "species": "dog",
        "preferred_size": "small",
        "preferred_age_group": "adult",
        "grooming_tolerance": "low",
        "noise_tolerance": "quiet",
        "daily_alone_hours": 5,
        "experience_level": "first_time",
    })

    assert query["species"] == "dog"
    assert query["housing_requirement"] == {"$in": ["apartment", "apartment_or_house"]}
    assert query["good_with_kids"] is True
    assert query["energy_level"] == {"$lte": 3}
    assert query["size"] == "small"
    assert query["age_group"] == "adult"
    assert query["grooming_needs"] == "low"
    assert query["noise_level"] == "quiet"
    assert query["alone_time_tolerance"] == {"$in": ["moderate", "high"]}
    assert query["experience_level_required"] == "first_time_friendly"


def test_chat_loads_signup_profile_and_passes_to_matchmaker(monkeypatch):
    class FakeSessionsCollection:
        async def find_one(self, query):
            return None

        async def update_one(self, query, update, upsert=False):
            return None

    class FakeProfilesCollection:
        async def find_one(self, query):
            return {
                "_id": "user_signup_1",
                "housing_type": "apartment",
                "has_children": True,
                "has_other_pets": False,
                "energy_budget": 2,
            }

    fake_db = FakeDatabase({
        "user_sessions": FakeSessionsCollection(),
        "user_profiles": FakeProfilesCollection(),
        "match_evaluations": FakeSessionsCollection(),
    })
    monkeypatch.setattr(chat, "get_async_db", lambda: fake_db)

    captured = {}

    def fake_run_turn(session_id, user_message, conversation_history=None, prior_constraints=None):
        captured["prior_constraints"] = prior_constraints
        return {
            "response_message": "Are you looking to adopt a dog or a cat?",
            "quick_replies": ["Looking for a Dog", "Looking for a Cat"],
            "is_complete": False,
            "candidate_matches": [],
            "evaluations": [],
            "extracted_constraints": prior_constraints,
        }

    monkeypatch.setattr(chat, "run_matchmaker_turn", fake_run_turn)
    prepare_test_app(monkeypatch)

    with TestClient(main.app) as client:
        resp = client.post(
            "/api/v1/chat/message",
            json={"session_id": "sess_1", "message": "Hi!", "user_id": "user_signup_1"},
        )

    assert resp.status_code == 200
    assert captured["prior_constraints"] == {
        "housing_type": "apartment",
        "has_children": True,
        "has_other_pets": False,
        "energy_budget": 2,
    }


def test_intake_never_repeats_signup_questions(monkeypatch):
    from app.services import nodes
    from app.services.state import LifestyleConstraints

    class RepeatingLLM:
        def with_structured_output(self, _):
            return self

        def invoke(self, _):
            return nodes.IntakeAnalysisOutput(
                extracted_constraints=LifestyleConstraints(species="dog"),
                is_sufficient_for_search=False,
                follow_up_question="What kind of living space do you have, an apartment or house?",
                suggested_quick_replies=["Apartment", "House with yard"],
            )

    monkeypatch.setattr(nodes, "get_chat_llm", lambda **_: RepeatingLLM())

    result = nodes.conversational_intake_node({
        "user_message": "I want a dog",
        "conversation_history": [],
        "extracted_constraints": {
            "housing_type": "apartment",
            "has_children": True,
            "has_other_pets": False,
            "energy_budget": 3,
        },
    })

    assert result["is_complete"] is False
    assert "living space" not in result["response_message"].lower()
    assert "age" in result["response_message"].lower()
    assert result["extracted_constraints"]["species"] == "dog"
    assert result["extracted_constraints"]["housing_type"] == "apartment"


def test_hybrid_search_fills_alternative_matches_when_only_one_exact_match(monkeypatch):
    pets_data = [
        {
            "_id": "pet_exact",
            "name": "Milo",
            "species": "dog",
            "size": "small",
            "age_group": "adult",
            "grooming_needs": "low",
            "noise_level": "quiet",
            "housing_requirement": "apartment",
            "good_with_kids": True,
            "energy_level": 2,
            "embedding": [1.0] * 768,
        },
        {
            "_id": "pet_alt_1",
            "name": "Waffles",
            "species": "dog",
            "size": "small",
            "age_group": "young",
            "grooming_needs": "low",
            "noise_level": "quiet",
            "housing_requirement": "apartment",
            "good_with_kids": True,
            "energy_level": 2,
            "embedding": [0.9] * 768,
        },
        {
            "_id": "pet_alt_2",
            "name": "Daisy",
            "species": "dog",
            "size": "small",
            "age_group": "young",
            "grooming_needs": "moderate",
            "noise_level": "quiet",
            "housing_requirement": "apartment",
            "good_with_kids": True,
            "energy_level": 2,
            "embedding": [0.8] * 768,
        },
    ]

    class InMemoryPetsCollection:
        def aggregate(self, pipeline):
            raise OperationFailure("Vector search is unavailable", 8000)

        def find(self, query):
            matched = []
            for p in pets_data:
                ok = True
                for k, v in query.items():
                    if isinstance(v, dict) and "$in" in v:
                        if p.get(k) not in v["$in"]:
                            ok = False
                    elif isinstance(v, dict) and "$lte" in v:
                        if p.get(k, 99) > v["$lte"]:
                            ok = False
                    elif p.get(k) != v:
                        ok = False
                if ok:
                    matched.append(p)
            return matched

    monkeypatch.setattr(retrieval, "generate_embedding", lambda _: [1.0] * 768)
    results = retrieval.hybrid_search_pets(
        query_text="small quiet adult dog",
        constraints={
            "species": "dog",
            "housing_type": "apartment",
            "has_children": True,
            "energy_budget": 2,
            "preferred_size": "small",
            "preferred_age_group": "adult",
            "grooming_tolerance": "low",
            "noise_tolerance": "quiet",
        },
        top_k=3,
        db=FakeDatabase({"pets": InMemoryPetsCollection()}),
    )

    assert [p["_id"] for p in results] == ["pet_exact", "pet_alt_1", "pet_alt_2"]


def test_generate_shelter_profile_saves_to_user_profile(monkeypatch):
    from app.routers import users

    class FakeProfilesCollection:
        def __init__(self):
            self.doc = {
                "_id": "user_p1",
                "name": "Alex",
                "email": "alex@example.com",
                "housing_type": "house_with_yard",
                "has_children": True,
                "has_other_pets": False,
                "energy_budget": 4,
            }
            self.updated = None

        async def find_one(self, query):
            return self.doc

        async def update_one(self, query, update):
            self.updated = (query, update)

    profiles = FakeProfilesCollection()
    monkeypatch.setattr(users, "get_async_db", lambda: FakeDatabase({"user_profiles": profiles}))

    resp = asyncio.run(users.generate_shelter_profile("user_p1"))

    assert resp.user_id == "user_p1"
    assert resp.adopter_name == "Alex"
    assert resp.housing_summary == "House with yard"
    assert "children" in resp.household_summary.lower()
    assert "4/5" in resp.activity_summary
    assert profiles.updated is not None
    assert profiles.updated[1]["$set"]["shelter_profile"]["housing_summary"] == "House with yard"


def test_update_user_profile_ignores_explicit_null_fields(monkeypatch):
    from app.routers import users
    from app.routers.users import UserProfileUpdateRequest

    class FakeProfilesCollection:
        def __init__(self):
            self.doc = {
                "_id": "user_null_test",
                "name": "Alex",
                "email": "alex@example.com",
                "housing_type": "apartment",
                "has_children": False,
                "has_other_pets": False,
                "energy_budget": 3,
            }

        async def find_one(self, query):
            return self.doc

        async def update_one(self, query, update):
            self.doc.update(update["$set"])

    profiles = FakeProfilesCollection()
    monkeypatch.setattr(users, "get_async_db", lambda: FakeDatabase({"user_profiles": profiles}))

    updated = asyncio.run(users.update_user_profile(
        "user_null_test",
        UserProfileUpdateRequest(name=None, email=None, housing_type="house_with_yard"),
    ))

    assert updated.name == "Alex"
    assert updated.email == "alex@example.com"
    assert updated.housing_type == "house_with_yard"







