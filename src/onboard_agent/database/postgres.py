from onboard_agent.database.schema import DEPARTMENTS_PER_FLOOR, MENTORS_FOR_INTERNS, Departments_Per_Floor, Mentors_For_Interns
from sqlmodel import Session, create_engine, SQLModel
import sqlite3

DB_FILE = "onboard_agent.sqlite"
DATABASE_URL = f"sqlite:///{DB_FILE}"
engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    with Session(engine) as session:
        yield session


def get_engine():
    return engine


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