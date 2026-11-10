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

