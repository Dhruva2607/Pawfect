"""
PawFect FastAPI Application.
[FROM MARKDOWN] matches Step 3.1, Step 3.2, Step 3.3, and Section 4.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database.indexes import setup_standard_indexes, setup_atlas_vector_search_index
from app.database.connection import close_clients, get_async_db
from app.routers import (
    chat_router,
    pets_router,
    matches_router,
    adoptions_router,
    users_router,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("pawfect")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle event handler: initializes indexes and vector search configuration on startup.
    """
    logger.info("Initializing PawFect API server...")
    try:
        await asyncio.to_thread(setup_standard_indexes)
        setup_atlas_vector_search_index()
        logger.info("PawFect database indexes verified.")
    except Exception:
        logger.exception("Database index setup failed; database-backed requests will remain unavailable.")

    yield

    logger.info("Shutting down PawFect API server...")
    await asyncio.to_thread(close_clients)


app = FastAPI(
    title="PawFect - AI Pet Matchmaker API",
    version="1.0.0",
    description="Backend API powering AI conversational matching, vector search, and adoption workflows.",
    lifespan=lifespan
)

# CORS middleware supporting Android Emulator (10.0.2.2) and local development
# [FROM MARKDOWN: Section 4 - Network Routing & Host Resolution]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api/v1 prefix [FROM MARKDOWN: Section 4]
app.include_router(chat_router, prefix="/api/v1")
app.include_router(pets_router, prefix="/api/v1")
app.include_router(matches_router, prefix="/api/v1")
app.include_router(adoptions_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    """Readiness check that includes the required MongoDB dependency."""
    try:
        await get_async_db().command("ping")
    except Exception:
        logger.exception("MongoDB readiness check failed.")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "service": "PawFect API",
                "version": "1.0.0",
                "database": "unavailable"
            }
        )

    return {
        "status": "healthy",
        "service": "PawFect API",
        "version": "1.0.0",
        "database": "connected"
    }


@app.get("/health/live", tags=["Health"])
async def liveness_check():
    """Liveness check that does not depend on external services."""
    return {
        "status": "alive",
        "service": "PawFect API",
        "version": "1.0.0"
    }
