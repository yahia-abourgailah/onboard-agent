"""seed additional departments hr the-marq eclatic

Revision ID: bc8254baa0d5
Revises: 649707933e75
Create Date: 2026-07-22 11:35:14.872764

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from database.schema import DEPARTMENTS

# revision identifiers, used by Alembic.
revision: str = "bc8254baa0d5"
down_revision: str | Sequence[str] | None = "649707933e75"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Departments added to schema.DEPARTMENTS after the initial seed (649707933e75).
# The data lives in schema.py (single source); this migration only owns these names.
NEW_DEPARTMENT_NAMES = ["Human Resources", "HR Operations", "The Marq", "Eclatic"]

departments = sa.table(
    "departments",
    sa.column("name", sa.String),
    sa.column("description", sa.String),
    sa.column("head", sa.String),
)


def upgrade() -> None:
    """Insert the new departments, skipping any already present by name.

    The prior seed migration reads the (mutable) DEPARTMENTS list at runtime, so a
    fresh database may already contain these four. Guarding by name keeps this safe
    both on fresh DBs (present -> skip) and on ones seeded before these rows were
    added (missing -> inserted).
    """
    rows = [d for d in DEPARTMENTS if d["name"] in NEW_DEPARTMENT_NAMES]
    bind = op.get_bind()
    existing = {r[0] for r in bind.execute(sa.select(departments.c.name))}
    to_insert = [d for d in rows if d["name"] not in existing]
    if to_insert:
        op.bulk_insert(departments, to_insert)


def downgrade() -> None:
    """Remove the departments this migration is responsible for."""
    op.execute(departments.delete().where(departments.c.name.in_(NEW_DEPARTMENT_NAMES)))
