"""
Database connection and initialization.

Currently backed by a local SQLite file so the project runs with no
external services. Swap the connection logic here for a real Postgres
connection (e.g. psycopg2 / SQLAlchemy) later — nothing outside this
file needs to change, since tools/sql_tool.py only calls run_query().
"""

import sqlite3

from onboard_agent.database.schema import SCHEMA_SQL, SAMPLE_ROWS

DB_PATH = "onboarding.db"


def init_db(path: str = DB_PATH) -> None:
    """Create the employees table and seed it if empty."""
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(SCHEMA_SQL)
    cur.execute("SELECT COUNT(*) FROM employees")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?)", SAMPLE_ROWS
        )
        conn.commit()
    conn.close()


def run_query(sql_query: str, path: str = DB_PATH) -> str:
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
