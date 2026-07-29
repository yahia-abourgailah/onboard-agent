from langchain_core.tools import tool

from database.postgres import run_query


@tool
def query_sql_db(sql_query: str) -> str:
    """Run a read-only SQL query against the interns' mentors and
    departments/facilities per floor databases and return the results.

    Write the SQL yourself based on the schema below.

    Table: mentors_for_interns
    Columns:
        id            INTEGER, primary key
        name          TEXT
        position      TEXT
        department    TEXT

    Table: departments
    Columns:
        id            INTEGER, primary key
        name          TEXT
        description   TEXT
        head          TEXT

    Table: departments_per_floor
    Columns:
        id:                           INTEGER, primary key
        floor:                        TEXT ("B2", "B1", "Ground", "First", "Second", "Third", "Fourth", "Fifth", "Sixth" only)
        departments_and_facilities:   TEXT

    Only SELECT statements are allowed. Always use SQLite syntax.
    If the question cannot be answered from this schema, do not call this
    tool at all — answer honestly instead.

    Args:
        sql_query: A complete, valid SQLite SELECT statement.
    """
    normalized = sql_query.strip().lower()

    if not normalized.startswith("select"):
        return "Error: only SELECT statements are allowed. No query was run."

    try:
        result = run_query(sql_query)
    except Exception as e:
        return f"Error: the query failed ({e}). Try rephrasing the question or check with HR."

    if not result:
        return "No matching records were found for that query."

    return result
