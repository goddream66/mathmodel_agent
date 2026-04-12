from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MemoryStore:
    db_path: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "db_path", Path(self.db_path))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS kv (
                    scope TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                    PRIMARY KEY (scope, agent, key)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scope TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        try:
            conn.execute("PRAGMA journal_mode=DELETE;")
            conn.execute("PRAGMA synchronous=NORMAL;")
        except sqlite3.OperationalError:
            # Some filesystems reject journal tuning on first-create; the
            # default SQLite settings are still good enough for this scaffold.
            pass
        return conn

    def set_shared(self, key: str, value: str) -> None:
        self._set(scope="shared", agent="*", key=key, value=value)

    def get_shared(self, key: str) -> str | None:
        return self._get(scope="shared", agent="*", key=key)

    def set_agent(self, agent: str, key: str, value: str) -> None:
        self._set(scope="agent", agent=agent, key=key, value=value)

    def get_agent(self, agent: str, key: str) -> str | None:
        return self._get(scope="agent", agent=agent, key=key)

    def set_shared_json(self, key: str, value: Any) -> None:
        self.set_shared(key, json.dumps(value, ensure_ascii=False))

    def get_shared_json(self, key: str) -> Any | None:
        v = self.get_shared(key)
        return json.loads(v) if v is not None else None

    def set_agent_json(self, agent: str, key: str, value: Any) -> None:
        self.set_agent(agent, key, json.dumps(value, ensure_ascii=False))

    def get_agent_json(self, agent: str, key: str) -> Any | None:
        v = self.get_agent(agent, key)
        return json.loads(v) if v is not None else None

    def append_event(self, scope: str, agent: str, type: str, payload: Any) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO events(scope, agent, type, payload) VALUES(?,?,?,?)",
                (scope, agent, type, json.dumps(payload, ensure_ascii=False)),
            )

    def _set(self, scope: str, agent: str, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO kv(scope, agent, key, value) VALUES(?,?,?,?)
                ON CONFLICT(scope, agent, key)
                DO UPDATE SET value=excluded.value, updated_at=datetime('now')
                """,
                (scope, agent, key, value),
            )

    def _get(self, scope: str, agent: str, key: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM kv WHERE scope=? AND agent=? AND key=?",
                (scope, agent, key),
            ).fetchone()
        return row[0] if row else None
