from sqlalchemy import text
from sqlalchemy.engine import Engine

# Map of tables that already exist in databases created before a column was added
# to the model. create_all() never alters existing tables, so these are applied
# here at startup, idempotently.
MISSING_COLUMN_FIXES = {
    "teams": {"created_at": "DATETIME"},
}


def _existing_columns(engine: Engine, table: str) -> set[str]:
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return {row[1] for row in rows}


def run_migrations(engine: Engine) -> None:
    """Add columns missing from pre-existing SQLite tables (idempotent)."""
    for table, columns in MISSING_COLUMN_FIXES.items():
        existing = _existing_columns(engine, table)
        for column, ddl_type in columns.items():
            if column in existing:
                continue
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}"))
                conn.execute(
                    text(f"UPDATE {table} SET {column} = CURRENT_TIMESTAMP WHERE {column} IS NULL")
                )