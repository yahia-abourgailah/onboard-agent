"""
Schema definition and sample seed data for the employee directory database.

Kept separate from postgres.py so the schema can be referenced (e.g. in
prompts) without importing any DB connection logic.
"""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    job_title TEXT NOT NULL,
    team TEXT NOT NULL,
    floor INTEGER NOT NULL,
    manager_name TEXT
);
"""

SAMPLE_ROWS = [
    (1, "Jane Doe", "jane.doe@company.com", "Engineering Manager", "Engineering", 3, None),
    (2, "John Smith", "john.smith@company.com", "Product Designer", "Design", 2, "Priya Nair"),
    (3, "Priya Nair", "priya.nair@company.com", "Design Lead", "Design", 2, None),
    (4, "Carlos Mendes", "carlos.mendes@company.com", "Backend Engineer", "Engineering", 3, "Jane Doe"),
    (5, "Amy Chen", "amy.chen@company.com", "Marketing Manager", "Marketing", 2, None),
]

# Human-readable schema description, used in the SQL tool's docstring and
# in the system/sql prompt so the LLM knows what it can query.
EMPLOYEES_TABLE_SCHEMA = """
Table: employees
Columns:
    id            INTEGER, primary key
    full_name     TEXT
    email         TEXT
    job_title     TEXT
    team          TEXT
    floor         INTEGER
    manager_name  TEXT (nullable, name of the employee's manager)
"""
