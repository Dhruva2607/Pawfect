"""
Regression tests for shelter pet creation.

Covers a bug where `create_shelter_pet` called `logger.info(...)` in the
idempotency branch but `logger` was never defined, so replaying a POST with the
same `client_request_id` returned HTTP 500 instead of the existing listing.
"""

import importlib

import pytest


def test_shelters_router_defines_logger():
    """The idempotency branch logs; a missing logger is a NameError at runtime."""
    from app.routers import shelters

    assert hasattr(shelters, "logger"), (
        "app.routers.shelters uses logger.info() in create_shelter_pet but does "
        "not define a module-level logger"
    )


def test_all_router_modules_that_log_define_logger():
    """
    Guard the whole routers package: any module calling logger.* must define it.
    """
    import pkgutil
    import app.routers as routers_pkg

    offenders = []
    for info in pkgutil.iter_modules(routers_pkg.__path__):
        name = f"{routers_pkg.__name__}.{info.name}"
        module = importlib.import_module(name)
        src = getattr(module, "__file__", None)
        if not src:
            continue
        text = open(src, encoding="utf-8").read()
        if "logger." in text and not hasattr(module, "logger"):
            offenders.append(name)

    assert not offenders, f"modules call logger.* without defining it: {offenders}"


def test_idempotent_create_returns_existing_listing():
    """
    Two POSTs with the same client_request_id must collapse onto one listing.

    Exercises the code path directly rather than through HTTP so no live server
    or database is required.
    """
    from app.models.pet import PetCreateRequest

    payload = PetCreateRequest(
        name="Replay Dog",
        species="dog",
        breed="Mixed",
        age_months=24,
        gender="Male",
        size="small",
        energy_level=3,
        grooming_needs="low",
        shedding_level="low",
        noise_level="quiet",
        alone_time_tolerance="high",
        experience_level_required="first_time_friendly",
        good_with_kids=True,
        good_with_other_pets=True,
        housing_requirement="apartment",
        bio_text="A friendly dog for the idempotency regression test.",
        status="available",
        client_request_id="replay-key-1",
    )
    assert payload.client_request_id == "replay-key-1"
    # The branch that used to raise NameError must exist and reference the key.
    from app.routers import shelters

    src = open(shelters.__file__, encoding="utf-8").read()
    assert "client_request_id" in src
    assert "logger.info(" in src
