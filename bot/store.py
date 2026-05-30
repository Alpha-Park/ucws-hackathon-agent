"""SQLite persistence for sessions, collections, posts, and traces."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "agent_state.db"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class AgentStore:
    def __init__(self, db_path: str | os.PathLike[str] | None = None):
        configured_path = db_path or os.getenv("GENPARK_AGENT_DB") or DEFAULT_DB_PATH
        self.db_path = Path(configured_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def _connection(self):
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._lock, self._connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    last_message TEXT,
                    pending_action TEXT,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, session_id)
                );

                CREATE TABLE IF NOT EXISTS collection_items (
                    user_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    product_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, product_id)
                );

                CREATE TABLE IF NOT EXISTS circle_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    status TEXT NOT NULL,
                    post_url TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS traces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def touch_session(
        self,
        user_id: str,
        session_id: str,
        *,
        last_message: str | None = None,
        pending_action: dict[str, Any] | None = None,
    ) -> None:
        pending = json.dumps(pending_action) if pending_action is not None else self.get_pending_action_raw(user_id, session_id)
        with self._lock, self._connection() as conn:
            conn.execute(
                """
                INSERT INTO sessions (user_id, session_id, last_message, pending_action, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, session_id) DO UPDATE SET
                    last_message = excluded.last_message,
                    pending_action = excluded.pending_action,
                    updated_at = excluded.updated_at
                """,
                (user_id, session_id, last_message, pending, utc_now()),
            )

    def get_pending_action_raw(self, user_id: str, session_id: str) -> str | None:
        with self._lock, self._connection() as conn:
            row = conn.execute(
                "SELECT pending_action FROM sessions WHERE user_id = ? AND session_id = ?",
                (user_id, session_id),
            ).fetchone()
        return row["pending_action"] if row else None

    def get_pending_action(self, user_id: str, session_id: str) -> dict[str, Any] | None:
        raw = self.get_pending_action_raw(user_id, session_id)
        if not raw:
            return None
        return json.loads(raw)

    def set_pending_action(self, user_id: str, session_id: str, action: dict[str, Any]) -> None:
        self.touch_session(user_id, session_id, pending_action=action)

    def clear_pending_action(self, user_id: str, session_id: str) -> None:
        with self._lock, self._connection() as conn:
            conn.execute(
                "UPDATE sessions SET pending_action = NULL, updated_at = ? WHERE user_id = ? AND session_id = ?",
                (utc_now(), user_id, session_id),
            )

    def add_to_collection(self, user_id: str, product: dict[str, Any]) -> bool:
        with self._lock, self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO collection_items (user_id, product_id, product_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, product["id"], json.dumps(product), utc_now()),
            )
            inserted = cursor.rowcount > 0
        return inserted

    def list_collection(self, user_id: str) -> list[dict[str, Any]]:
        with self._lock, self._connection() as conn:
            rows = conn.execute(
                "SELECT product_json FROM collection_items WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        return [json.loads(row["product_json"]) for row in rows]

    def remove_from_collection(self, user_id: str, product_id: str) -> bool:
        with self._lock, self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM collection_items WHERE user_id = ? AND product_id = ?",
                (user_id, product_id),
            )
            removed = cursor.rowcount > 0
        return removed

    def save_post(self, user_id: str, content: str, status: str, post_url: str | None = None) -> int:
        with self._lock, self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO circle_posts (user_id, content, status, post_url, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, content, status, post_url, utc_now()),
            )
            post_id = int(cursor.lastrowid)
        return post_id

    def save_trace(self, user_id: str, session_id: str, message: str, response: dict[str, Any]) -> None:
        with self._lock, self._connection() as conn:
            conn.execute(
                """
                INSERT INTO traces (user_id, session_id, message, response_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, session_id, message, json.dumps(response), utc_now()),
            )
