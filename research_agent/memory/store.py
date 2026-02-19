"""Simple SQLite persistence for research runs."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from research_agent.config import settings
from research_agent.graph.state import AgentState


class RunStore:
    """Store and retrieve completed research runs."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or settings.db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    report TEXT NOT NULL,
                    state_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def save(self, state: AgentState) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO runs (run_id, question, report, state_json, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    state.run_id,
                    state.question,
                    state.report,
                    state.model_dump_json(),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

    def get(self, run_id: str) -> AgentState | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT state_json FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
        if row is None:
            return None
        return AgentState.model_validate_json(row[0])

    def list_runs(self, limit: int = 20) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT run_id, question, created_at FROM runs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [{"run_id": r[0], "question": r[1], "created_at": r[2]} for r in rows]
