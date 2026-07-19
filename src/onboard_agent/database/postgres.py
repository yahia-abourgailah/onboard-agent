"""
Database connection, initialization, and read-only query helper.

Backed by a local SQLite file via SQLModel. Schema is owned by Alembic
(see migrations/); init_db() below is a self-bootstrapping convenience for
local/dev runs — it creates the tables and seeds reference data if the DB is
empty, so the app works on a fresh checkout without a manual `alembic upgrade`.
Both paths are idempotent: init_db() only seeds when a table is empty.
"""

import sqlite3
from collections.abc import Iterator

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine, select

from onboard_agent.database.schema import (
    DEPARTMENTS_PER_FLOOR,
    MENTORS_FOR_INTERNS,
    Departments_Per_Floor,
    Mentors_For_Interns,
)

DB_FILE = "onboard_agent.sqlite"
DATABASE_URL = f"sqlite:///{DB_FILE}"
engine = create_engine(DATABASE_URL, echo=False)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def get_engine() -> Engine:
    return engine


def init_db() -> None:
    """Create tables and seed reference data if empty. Idempotent."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        if session.exec(select(Departments_Per_Floor)).first() is None:
            session.add_all(Departments_Per_Floor(**row) for row in DEPARTMENTS_PER_FLOOR)
        if session.exec(select(Mentors_For_Interns)).first() is None:
            session.add_all(Mentors_For_Interns(**row) for row in MENTORS_FOR_INTERNS)
        session.commit()


def run_query(sql_query: str, path: str = DB_FILE) -> str:
    """
    Execute a read-only SELECT query and return results as plain text.
    Raises no exceptions to the caller — errors are returned as strings
    so the calling tool can hand them straight back to the LLM.
    """
    normalized = sql_query.strip().lower()
    if not normalized.startswith("select"):
        return "Only SELECT queries are allowed."

    try:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql_query)
        rows = cur.fetchall()
        conn.close()
    except sqlite3.Error as e:
        return f"SQL error: {e}"

    if not rows:
        return "No matching records found."

    columns = rows[0].keys()
    lines = [", ".join(columns)]
    for row in rows:
        lines.append(", ".join(str(row[c]) for c in columns))
    return "\n".join(lines)
