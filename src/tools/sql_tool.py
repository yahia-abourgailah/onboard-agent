from langchain_core.tools import tool

from database.postgres import run_query


@tool
def query_sql_db(sql_query: str) -> str:
    """
    Run a read-only SQL query against the interns' mentors and departments/facilities per floor databases and
    return the results. Write the SQL yourself based on the schema below.

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
        id                            INTEGER, primary key
        floor                         TEXT ("B2", "B1", "Ground", "First", "Second", "Third", "Fourth", "Fifth", "Sixth" only)
        departments_and_facilities    TEXT 

    Only SELECT statements are allowed. Always use SQLite syntax.

    Args:
        sql_query: A complete, valid SQLite SELECT statement.
    """
    return run_query(sql_query)
