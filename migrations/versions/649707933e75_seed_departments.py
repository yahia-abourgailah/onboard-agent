"""seed departments

Revision ID: 649707933e75
Revises: 952747231624
Create Date: 2026-07-20 15:56:08.367606

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from database.schema import DEPARTMENTS

# revision identifiers, used by Alembic.
revision: str = "649707933e75"
down_revision: str | Sequence[str] | None = "952747231624"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

departments_table = sa.table(
    "departments",
    sa.column("name", sa.String),
    sa.column("description", sa.String),
    sa.column("head", sa.String),
)


def upgrade() -> None:
    """Upgrade schema."""
    op.bulk_insert(departments_table, DEPARTMENTS)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        departments_table.delete().where(
            departments_table.c.name.in_([row["name"] for row in DEPARTMENTS])
        )
    )
