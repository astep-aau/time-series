"""Remove start_date from dataset model

Revision ID: f6fbdc23912f
Revises: a2a07af82d7b
Create Date: 2025-12-03 11:36:09.743917

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6fbdc23912f"
down_revision: Union[str, Sequence[str], None] = "a2a07af82d7b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column("datasets", "start_date", schema="timeseries")
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "datasets",
        sa.Column("start_date", postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        schema="timeseries",
    )
    op.execute("UPDATE timeseries.datasets SET start_date = '1970-01-01 00:00:00'")
    op.alter_column("datasets", "start_date", nullable=False, schema="timeseries")
    # ### end Alembic commands ###
