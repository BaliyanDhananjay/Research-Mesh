"""Small SQLite repository for the single-user MVP."""

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from research_mesh.domain.models import (
    EvidenceSnippet,
    Report,
    ResearchRun,
    RunEvent,
    RunStatus,
    SourceDocument,
)


class SQLiteRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        if str(self.database_path) != ":memory:":
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False: a run is created on the request thread and
        # executed on a background thread, sequentially, never concurrently.
        self._connection = sqlite3.connect(self.database_path, check_same_thread=False)
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
            CREATE TABLE IF NOT EXISTS sources (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL REFERENCES runs(id),
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                source_type TEXT NOT NULL,
                domain TEXT NOT NULL,
                quality_score REAL NOT NULL,
                content_hash TEXT
            );
            CREATE TABLE IF NOT EXISTS evidence_snippets (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL REFERENCES sources(id),
                text TEXT NOT NULL,
                locator TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL REFERENCES runs(id),
                report_json TEXT NOT NULL
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
            "UPDATE runs SET status = ?, updated_at = ?, error = ? WHERE id = ?",
            (status.value, datetime.now(UTC).isoformat(), error, run_id),
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

    def list_events_for_run(self, run_id: str) -> list[RunEvent]:
        rows = self._connection.execute(
            "SELECT * FROM run_events WHERE run_id = ? ORDER BY created_at ASC",
            (run_id,),
        ).fetchall()
        return [
            RunEvent.model_validate(
                {
                    "id": row["id"],
                    "run_id": row["run_id"],
                    "event_type": row["event_type"],
                    "message": row["message"],
                    "created_at": row["created_at"],
                }
            )
            for row in rows
        ]

    def close(self) -> None:
        self._connection.close()

    def save_source(self, source: SourceDocument) -> None:
        self._connection.execute(
            """
            INSERT OR REPLACE INTO sources
            (id, run_id, url, title, source_type, domain, quality_score, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(source.id),
                str(source.run_id),
                str(source.url),
                source.title,
                source.source_type,
                source.domain,
                source.quality_score,
                source.content_hash,
            ),
        )
        self._connection.commit()

    def list_sources_for_run(self, run_id: str) -> list[SourceDocument]:
        rows = self._connection.execute(
            "SELECT * FROM sources WHERE run_id = ? ORDER BY quality_score DESC",
            (run_id,),
        ).fetchall()
        return [
            SourceDocument.model_validate(
                {
                    "id": row["id"],
                    "run_id": row["run_id"],
                    "url": row["url"],
                    "title": row["title"],
                    "source_type": row["source_type"],
                    "domain": row["domain"],
                    "quality_score": row["quality_score"],
                    "content_hash": row["content_hash"],
                }
            )
            for row in rows
        ]

    def save_evidence(self, evidence: EvidenceSnippet) -> None:
        self._connection.execute(
            """
            INSERT OR REPLACE INTO evidence_snippets (id, source_id, text, locator)
            VALUES (?, ?, ?, ?)
            """,
            (str(evidence.id), str(evidence.source_id), evidence.text, evidence.locator),
        )
        self._connection.commit()

    def list_evidence_for_source(self, source_id: str) -> list[EvidenceSnippet]:
        rows = self._connection.execute(
            "SELECT * FROM evidence_snippets WHERE source_id = ?",
            (source_id,),
        ).fetchall()
        return [
            EvidenceSnippet.model_validate(
                {
                    "id": row["id"],
                    "source_id": row["source_id"],
                    "text": row["text"],
                    "locator": row["locator"],
                }
            )
            for row in rows
        ]

    def save_report(self, report: Report) -> None:
        self._connection.execute(
            "INSERT OR REPLACE INTO reports (id, run_id, report_json) VALUES (?, ?, ?)",
            (str(report.id), str(report.run_id), report.model_dump_json()),
        )
        self._connection.commit()

    def get_report_for_run(self, run_id: str) -> Report | None:
        row = self._connection.execute(
            "SELECT report_json FROM reports WHERE run_id = ? ORDER BY rowid DESC LIMIT 1",
            (run_id,),
        ).fetchone()
        if row is None:
            return None
        return Report.model_validate(json.loads(row["report_json"]))
