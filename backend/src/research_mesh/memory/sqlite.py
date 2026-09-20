"""Small SQLite repository for the single-user MVP."""

import json
import sqlite3
from pathlib import Path

from research_mesh.domain.models import ResearchRun, RunEvent, RunStatus


class SQLiteRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        if str(self.database_path) != ":memory:":
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.database_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    def _create_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                request_json TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                error TEXT
            );
            CREATE TABLE IF NOT EXISTS run_events (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL REFERENCES runs(id),
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        self._connection.commit()

    def save_run(self, run: ResearchRun) -> None:
        self._connection.execute(
            """
            INSERT OR REPLACE INTO runs
            (id, request_json, status, created_at, updated_at, error)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(run.id),
                run.request.model_dump_json(),
                run.status.value,
                run.created_at.isoformat(),
                run.updated_at.isoformat(),
                run.error,
            ),
        )
        self._connection.commit()

    def get_run(self, run_id: str) -> ResearchRun | None:
        row = self._connection.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            return None
        return ResearchRun.model_validate(
            {
                "id": row["id"],
                "request": json.loads(row["request_json"]),
                "status": row["status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "error": row["error"],
            }
        )

    def update_status(self, run_id: str, status: RunStatus, error: str | None = None) -> None:
        self._connection.execute(
            "UPDATE runs SET status = ?, updated_at = datetime('now'), error = ? WHERE id = ?",
            (status.value, error, run_id),
        )
        self._connection.commit()

    def add_event(self, event: RunEvent) -> None:
        self._connection.execute(
            "INSERT INTO run_events "
            "(id, run_id, event_type, message, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                str(event.id),
                str(event.run_id),
                event.event_type,
                event.message,
                event.created_at.isoformat(),
            ),
        )
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()
