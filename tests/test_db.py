"""
Unit tests for app/db.py.

All tests use an in-memory SQLite database (via tmp_path or ":memory:") so
they are fully isolated, fast, and leave no files on disk.
"""

import sqlite3
from pathlib import Path

import pytest

import json

from app.db import init_db, save_feedback, save_generation, save_session, TAG_MAX_LEN

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "test.db"
    init_db(db_path)
    return db_path


def _sample_generation(db_path: Path, condition: str = "baseline") -> int:
    return save_generation(
        condition=condition,
        model="test-model",
        system_prompt="You are a test.",
        user_prompt="Write something.",
        temperature=0.85,
        body=["Para 1.", "Para 2.", "Para 3."],
        endings=["End A.", "End B."],
        timing_ms=1234,
        db_path=db_path,
    )


# ---------------------------------------------------------------------------
# init_db
# ---------------------------------------------------------------------------

def test_init_db_creates_all_three_tables(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    conn.close()
    assert "generation" in tables
    assert "session" in tables
    assert "feedback" in tables


def test_init_db_is_idempotent(tmp_path):
    """Calling init_db twice should not raise."""
    db_path = tmp_path / "test.db"
    init_db(db_path)
    init_db(db_path)


# ---------------------------------------------------------------------------
# save_generation
# ---------------------------------------------------------------------------

def test_save_generation_returns_integer_id(tmp_path):
    db_path = _fresh_db(tmp_path)
    gen_id = _sample_generation(db_path)
    assert isinstance(gen_id, int)
    assert gen_id >= 1


def test_save_generation_increments_id(tmp_path):
    db_path = _fresh_db(tmp_path)
    id1 = _sample_generation(db_path)
    id2 = _sample_generation(db_path)
    assert id2 > id1


def test_save_generation_stores_all_fields(tmp_path):
    db_path = _fresh_db(tmp_path)
    gen_id = save_generation(
        condition="harness",
        model="my-model",
        system_prompt="sys prompt",
        user_prompt="user prompt",
        temperature=0.9,
        body=["p1", "p2"],
        endings=["e1", "e2"],
        timing_ms=999,
        db_path=db_path,
    )
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT * FROM generation WHERE id = ?", (gen_id,)
    ).fetchone()
    conn.close()

    assert row is not None
    cols = {desc[0]: val for desc, val in zip(
        conn.execute("SELECT * FROM generation WHERE id=?", (gen_id,)).description
        if False else [],  # avoid reuse of closed conn; use index below
        []
    )}
    # Re-query with column names via row_factory
    import sqlite3 as _sqlite3
    conn2 = _sqlite3.connect(db_path)
    conn2.row_factory = _sqlite3.Row
    row2 = conn2.execute("SELECT * FROM generation WHERE id = ?", (gen_id,)).fetchone()
    conn2.close()
    assert row2["condition"] == "harness"
    assert row2["model"] == "my-model"
    assert row2["system_prompt"] == "sys prompt"
    assert row2["user_prompt"] == "user prompt"
    assert row2["temperature"] == 0.9
    assert row2["timing_ms"] == 999


def test_save_generation_candidates_and_scores_nullable(tmp_path):
    db_path = _fresh_db(tmp_path)
    gen_id = _sample_generation(db_path)
    import sqlite3 as _sqlite3
    conn = _sqlite3.connect(db_path)
    conn.row_factory = _sqlite3.Row
    row = conn.execute("SELECT candidates, scores FROM generation WHERE id=?", (gen_id,)).fetchone()
    conn.close()
    assert row["candidates"] is None
    assert row["scores"] is None


# ---------------------------------------------------------------------------
# save_session
# ---------------------------------------------------------------------------

def test_save_session_returns_integer_id(tmp_path):
    db_path = _fresh_db(tmp_path)
    bid = _sample_generation(db_path, "baseline")
    hid = _sample_generation(db_path, "harness")
    session_id = save_session(generation_ids=[bid, hid], db_path=db_path)
    assert isinstance(session_id, int)
    assert session_id >= 1


def test_save_session_stores_generation_ids_as_json_array(tmp_path):
    db_path = _fresh_db(tmp_path)
    bid = _sample_generation(db_path, "baseline")
    hid = _sample_generation(db_path, "harness")
    session_id = save_session(generation_ids=[bid, hid], db_path=db_path)
    import sqlite3 as _sqlite3
    conn = _sqlite3.connect(db_path)
    conn.row_factory = _sqlite3.Row
    row = conn.execute("SELECT * FROM session WHERE id=?", (session_id,)).fetchone()
    conn.close()
    stored = json.loads(row["generation_ids"])
    assert stored == [bid, hid]


# ---------------------------------------------------------------------------
# save_feedback
# ---------------------------------------------------------------------------

def test_save_feedback_returns_integer_id(tmp_path):
    db_path = _fresh_db(tmp_path)
    bid = _sample_generation(db_path)
    fb_id = save_feedback(generation_id=bid, rating=4, tag="evocative", db_path=db_path)
    assert isinstance(fb_id, int)
    assert fb_id >= 1


def test_save_feedback_stores_all_fields(tmp_path):
    db_path = _fresh_db(tmp_path)
    bid = _sample_generation(db_path)
    fb_id = save_feedback(
        generation_id=bid,
        rating=5,
        tag="melancholy",
        db_path=db_path,
    )
    import sqlite3 as _sqlite3
    conn = _sqlite3.connect(db_path)
    conn.row_factory = _sqlite3.Row
    row = conn.execute("SELECT * FROM feedback WHERE id=?", (fb_id,)).fetchone()
    conn.close()
    assert row["generation_id"] == bid
    assert row["rating"] == 5
    assert row["tag"] == "melancholy"


def test_save_feedback_rating_nullable(tmp_path):
    db_path = _fresh_db(tmp_path)
    bid = _sample_generation(db_path)
    fb_id = save_feedback(generation_id=bid, db_path=db_path)
    import sqlite3 as _sqlite3
    conn = _sqlite3.connect(db_path)
    conn.row_factory = _sqlite3.Row
    row = conn.execute("SELECT * FROM feedback WHERE id=?", (fb_id,)).fetchone()
    conn.close()
    assert row["rating"] is None
    assert row["tag"] is None


def test_save_feedback_tag_too_long_raises(tmp_path):
    db_path = _fresh_db(tmp_path)
    bid = _sample_generation(db_path)
    with pytest.raises(ValueError, match="tag"):
        save_feedback(generation_id=bid, tag="x" * (TAG_MAX_LEN + 1), db_path=db_path)


def test_save_feedback_tag_at_max_length_ok(tmp_path):
    db_path = _fresh_db(tmp_path)
    bid = _sample_generation(db_path)
    fb_id = save_feedback(generation_id=bid, tag="x" * TAG_MAX_LEN, db_path=db_path)
    assert fb_id >= 1
