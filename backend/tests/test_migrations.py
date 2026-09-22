import os
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text

from app.database.migrations import run_migrations


def _new_engine(tmp_path):
    db_path = tmp_path / "stale.db"
    return create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})


def _make_stale_teams(engine):
    """Create a `teams` table as it existed before created_at was added."""
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE teams (id INTEGER PRIMARY KEY, name VARCHAR(255) NOT NULL, "
            "sport_id INTEGER NOT NULL, coach_id INTEGER NOT NULL)"
        ))
        conn.execute(text(
            "INSERT INTO teams (id, name, sport_id, coach_id) VALUES (1, 'Volei A', 1, 1)"
        ))


def test_migration_adds_missing_column(tmp_path):
    engine = _new_engine(tmp_path)
    _make_stale_teams(engine)

    run_migrations(engine)

    with engine.connect() as conn:
        columns = {row[1] for row in conn.execute(text("PRAGMA table_info(teams)")).fetchall()}
        row = conn.execute(text("SELECT name, created_at FROM teams WHERE id = 1")).fetchone()

    assert "created_at" in columns
    assert row[0] == "Volei A"
    assert row[1] is not None
    engine.dispose()


def test_migration_is_idempotent(tmp_path):
    engine = _new_engine(tmp_path)
    _make_stale_teams(engine)

    run_migrations(engine)
    run_migrations(engine)

    with engine.connect() as conn:
        columns = {row[1] for row in conn.execute(text("PRAGMA table_info(teams)")).fetchall()}
    assert "created_at" in columns
    engine.dispose()


def test_migration_noop_on_actual_db(tmp_path):
    engine = _new_engine(tmp_path)
    _make_stale_teams(engine)
    run_migrations(engine)

    pre = sqlite3.connect(engine.url.database).total_changes
    run_migrations(engine)
    assert sqlite3.connect(engine.url.database).total_changes == pre
    engine.dispose()