"""Centralised configuration loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_host: str = "http://ollama:11434"
    ollama_model: str = "gemma3:12b"
    ollama_timeout_seconds: int = 300
    log_level: str = "INFO"

    # Agent defaults
    max_iters: int = 6
    timebox_minutes: int = 5
    tool_call_limit: int = 30

    # PDF upload limits
    pdf_max_size_mb: int = 20
    pdf_max_extract_chars: int = 40_000

    # Persistence
    db_path: str = "runs/research_agent.db"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
