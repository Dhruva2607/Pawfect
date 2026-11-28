"""
Tests for `app.scripts.seed_demo_data`:
- Determinism with fixed random seed
- All Section 6 integrity checks, coverage matrix, and persona match density
- Idempotency: a second write_to_db run creates zero new documents
"""

from copy import deepcopy

from app.scripts import seed_demo_data as demo


class FakeSyncCol:
    def __init__(self):
        self.docs = {}

    def create_index(self, *args, **kwargs):
        return kwargs.get("name", "idx")

    def list_search_indexes(self):
        return []

    def create_search_index(self, *args, **kwargs):
        return None

    def delete_many(self, query):
        to_del = [
            k for k, d in self.docs.items()
            if all(d.get(qk) == qv for qk, qv in query.items())
        ]
        for k in to_del:
            del self.docs[k]

        class _Res:
            deleted_count = len(to_del)

        return _Res()

    def update_one(self, query, update, upsert=False):
        doc_id = query["_id"]
        if doc_id in self.docs:
            self.docs[doc_id].update(deepcopy(update["$set"]))
        elif upsert:
            self.docs[doc_id] = deepcopy(update["$set"])


class FakeSyncDB:
    def __init__(self):
        self.cols = {}

    def __getitem__(self, name):
        if name not in self.cols:
            self.cols[name] = FakeSyncCol()
        return self.cols[name]


def test_demo_generation_is_deterministic():
    run1 = demo.generate_all(seed=42)
    run2 = demo.generate_all(seed=42)

    assert [s["_id"] for s in run1["shelters"]] == [s["_id"] for s in run2["shelters"]]
    assert [p["_id"] for p in run1["all_pets"]] == [p["_id"] for p in run2["all_pets"]]
    assert [a["_id"] for a in run1["apps"]] == [a["_id"] for a in run2["apps"]]
    assert [n["_id"] for n in run1["notifs"]] == [n["_id"] for n in run2["notifs"]]


def test_demo_integrity_coverage_and_density():
    data = demo.generate_all(seed=42)
    report = demo.verify_dataset_integrity(
        shelters=data["shelters"],
        pets=data["all_pets"],
        users=data["users"],
        sessions=data["sessions"],
        evaluations=data["evaluations"],
        apps=data["apps"],
        notifs=data["notifs"],
        skip_embeddings=True,
    )
    assert len(data["shelters"]) == 8
    assert len(data["all_pets"]) == 120
    assert len(data["users"]) == 30
    assert len(data["apps"]) == 60
    assert report["niche_match_count"] <= 2

    # Busiest shelter has 25+ pets and 20+ apps; unverified shelter_demo_08 has 3 pets and 0 apps
    s1_pets = [p for p in data["all_pets"] if p["shelter_id"] == "shelter_demo_01"]
    s1_apps = [a for a in data["apps"] if a["shelter_id"] == "shelter_demo_01"]
    s8_pets = [p for p in data["all_pets"] if p["shelter_id"] == "shelter_demo_08"]
    s8_apps = [a for a in data["apps"] if a["shelter_id"] == "shelter_demo_08"]
    assert len(s1_pets) >= 25
    assert len(s1_apps) >= 20
    assert 2 <= len(s8_pets) <= 4
    assert len(s8_apps) == 0


def test_demo_write_to_db_is_idempotent(monkeypatch):
    monkeypatch.setattr(demo, "setup_standard_indexes", lambda db: {})
    monkeypatch.setattr(demo, "setup_atlas_vector_search_index", lambda db: True)

    fake_db = FakeSyncDB()
    data1 = demo.generate_all(seed=42)
    demo.write_to_db(fake_db, data1, skip_embeddings=True)

    counts_after_first = {name: len(col.docs) for name, col in fake_db.cols.items()}

    # Second run creates zero new documents
    data2 = demo.generate_all(seed=42)
    demo.write_to_db(fake_db, data2, skip_embeddings=True)
    counts_after_second = {name: len(col.docs) for name, col in fake_db.cols.items()}

    assert counts_after_first == counts_after_second
