"""seed departments and mentors data

Revision ID: 3e488ddc5555
Revises: a96c2c884ccb
Create Date: 2026-07-15 16:26:56.882999

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from src.onboard_agent.database.schema import DEPARTMENTS_PER_FLOOR, MENTORS_FOR_INTERNS


# revision identifiers, used by Alembic.
revision: str = '3e488ddc5555'
down_revision: Union[str, Sequence[str], None] = 'a96c2c884ccb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

departments_per_floor_table = sa.table(
    "departments_per_floor",
    sa.column("floor", sa.String),
    sa.column("departments_and_facilities", sa.String),
)

mentors_for_interns_table = sa.table(
    "mentors_for_interns",
    sa.column("name", sa.String),
    sa.column("position", sa.String),
    sa.column("department", sa.String),
)

def upgrade() -> None:
    """Upgrade schema."""
    op.bulk_insert(departments_per_floor_table, DEPARTMENTS_PER_FLOOR)
    op.bulk_insert(mentors_for_interns_table, MENTORS_FOR_INTERNS)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        departments_per_floor_table.delete().where(
            departments_per_floor_table.c.floor.in_(
                [row["floor"] for row in DEPARTMENTS_PER_FLOOR]
            )
        )
    )
    op.execute(
        mentors_for_interns_table.delete().where(
            mentors_for_interns_table.c.name.in_(
                [row["name"] for row in MENTORS_FOR_INTERNS]
            )
        )
    )
