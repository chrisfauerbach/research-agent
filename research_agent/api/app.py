"""FastAPI application."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from research_agent.api.routers import research

app = FastAPI(
    title="Research Agent",
    version="0.1.0",
    description="Autonomous technical research agent powered by LangGraph and Ollama.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research.router, prefix="/api")


@app.get("/")
async def index() -> dict:
    return {"message": "Research Agent API. Use the frontend at http://localhost:3000"}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
