"""FastAPI application entry point."""

import logging

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.models import HealthResponse
from app.routes import evaluate, query, suggestions, topics, upload
from app.services.embeddings import warm_up

logging.basicConfig(
level=settings.log_level,
format="%(asctime)s %(levelname)-8s %(name)s :: %(message)s",
)
logger = logging.getLogger(__name__)
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown hooks."""
    settings.ensure_dirs()
    logger.info("Loading models -- first run downloads ~170 MB, please wait...")
    warm_up()
    logger.info("Ready.")
    yield
    logger.info("Shutting down.")
app = FastAPI(
title="Single-Source Retrieval",
description="Single-document RAG assistant with re-ranking and RAGAS evaluation.",
version="1.0.0",
lifespan=lifespan,
)
app.add_middleware(
CORSMiddleware,
allow_origins=settings.cors_origins,
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)
for module in (upload, query, suggestions, topics, evaluate):
    app.include_router(module.router)

@app.get("/health", response_model=HealthResponse, tags=["meta"])
async def health() -> HealthResponse:
    return HealthResponse(
    embedding_model=settings.embedding_model,
    llm_model=settings.llm_model,
    )

# Serve the vanilla frontend from the same origin as the API.
# Mounted last so it never shadows an /api route.
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
    logger.info("Serving frontend from %s", FRONTEND_DIR)
