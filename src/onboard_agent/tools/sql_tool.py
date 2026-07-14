from langchain_core.tools import tool

from onboard_agent.database.postgres import run_query


@tool
def query_sql_db(sql_query: str) -> str:
    """
    Run a read-only SQL query against the employee directory database and
    return the results. Write the SQL yourself based on the schema below.

    Table: employees
    Columns:
        id            INTEGER, primary key
        full_name     TEXT
        email         TEXT
        job_title     TEXT
        team          TEXT
        floor         INTEGER
        manager_name  TEXT (nullable, name of the employee's manager)

    Only SELECT statements are allowed. Always use SQLite syntax.

    Args:
        sql_query: A complete, valid SQLite SELECT statement.
    """
    return run_query(sql_query)
