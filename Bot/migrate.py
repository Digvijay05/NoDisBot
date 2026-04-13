"""
Safe schema migration for NoDisBot.

Handles two cases:
1. Fresh database — create_all() builds everything from scratch.
2. Existing database — ALTER TABLE adds new columns one by one.
   SQLite raises OperationalError if a column already exists, which we catch and skip.
"""

from database import SessionLocal, engine
import models


# New columns added to the 'clients' table in Phase 1.
# Format: (column_name, column_type_sql, default_value_sql_or_None)
_NEW_CLIENT_COLUMNS = [
    ("ollama_base_url", "TEXT", None),
    ("ollama_model", "TEXT", None),
    ("task_title_property", "TEXT", "'Task'"),
    ("task_status_property", "TEXT", "'Status'"),
    ("task_assignee_property", "TEXT", "'Assignee'"),
    ("task_description_property", "TEXT", "'Description'"),
    ("task_priority_property", "TEXT", "'Priority'"),
    ("task_due_date_property", "TEXT", "'Due Date'"),
    ("task_tags_property", "TEXT", "'Tags'"),
    ("archive_mode", "TEXT", "'checkbox'"),
]


def run_migrations():
    """Run all pending migrations, then ensure tables exist."""

    # 1. Create any brand-new tables (e.g. assignee_mappings)
    models.Base.metadata.create_all(bind=engine)

    # 2. Add new columns to existing tables (safe for SQLite)
    _add_columns_to_clients()

    print("[migrate] Migrations complete.")


def _add_columns_to_clients():
    """Attempt to add each new column to the clients table.

    SQLite will raise if the column already exists — we catch that and move on.
    """
    conn = engine.connect()
    try:
        for col_name, col_type, default in _NEW_CLIENT_COLUMNS:
            default_clause = f" DEFAULT {default}" if default else ""
            sql = f"ALTER TABLE clients ADD COLUMN {col_name} {col_type}{default_clause}"
            try:
                conn.execute(sql)
                print(f"[migrate] Added column: clients.{col_name}")
            except Exception:
                # Column already exists — skip silently
                pass
    finally:
        conn.close()


if __name__ == "__main__":
    run_migrations()