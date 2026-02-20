"""
Database layer: SQLite via stdlib sqlite3.

Single source of truth for all experiment data:
  generation — one row per LLM call (with full prompt snapshots)
  session    — groups N generations shown together (generation_ids stored as JSON array)
  feedback   — one row per generation rated by the user

The DB file path comes from config.DB_PATH (default: data/experiment.db).
Call init_db() once at app startup to create tables if they don't exist.
"""

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, Optional

from app import config

logger = logging.getLogger(__name__)

TAG_MAX_LEN = 120


def _db_path() -> Path:
    p = Path(config.DB_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


@contextmanager
def _connect(db_path: Optional[Path] = None) -> Generator[sqlite3.Connection, None, None]:
    path = db_path or _db_path()
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Optional[Path] = None) -> None:
    """Create all tables if they do not already exist."""
    with _connect(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS generation (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                ts            TEXT    NOT NULL,
                condition     TEXT    NOT NULL,
                model         TEXT    NOT NULL,
                system_prompt TEXT    NOT NULL,
                user_prompt   TEXT    NOT NULL,
                temperature   REAL    NOT NULL,
                body          TEXT    NOT NULL,
                endings       TEXT    NOT NULL,
                timing_ms     INTEGER NOT NULL,
                candidates    TEXT,
                scores        TEXT
            );

            CREATE TABLE IF NOT EXISTS session (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                ts             TEXT    NOT NULL,
                generation_ids TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                ts            TEXT    NOT NULL,
                generation_id INTEGER NOT NULL REFERENCES generation(id),
                rating        INTEGER,
                tag           TEXT
            );
        """)


def save_generation(
    *,
    condition: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    body: list[str],
    endings: list[str],
    timing_ms: int,
    candidates: Optional[list] = None,
    scores: Optional[list] = None,
    db_path: Optional[Path] = None,
) -> int:
    """Insert a generation row and return its id."""
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO generation
                (ts, condition, model, system_prompt, user_prompt, temperature,
                 body, endings, timing_ms, candidates, scores)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                condition,
                model,
                system_prompt,
                user_prompt,
                temperature,
                json.dumps(body),
                json.dumps(endings),
                timing_ms,
                json.dumps(candidates) if candidates is not None else None,
                json.dumps(scores) if scores is not None else None,
            ),
        )
        return cur.lastrowid


def save_session(
    *,
    generation_ids: list,
    db_path: Optional[Path] = None,
) -> int:
    """Insert a session row grouping N generation rows and return its id."""
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO session (ts, generation_ids)
            VALUES (?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                json.dumps(generation_ids),
            ),
        )
        return cur.lastrowid


def save_feedback(
    *,
    generation_id: int,
    rating: Optional[int] = None,
    tag: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> int:
    """Insert a feedback row for a single generation and return its id."""
    if tag is not None and len(tag) > TAG_MAX_LEN:
        raise ValueError(f"tag must be at most {TAG_MAX_LEN} characters")
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO feedback (ts, generation_id, rating, tag)
            VALUES (?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                generation_id,
                rating,
                tag,
            ),
        )
        return cur.lastrowid
