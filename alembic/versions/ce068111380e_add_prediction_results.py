"""add prediction_results table

Revision ID: ce068111380e
Revises: 3571e1ef04d0
Create Date: 2025-12-15 18:41:00.629950

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ce068111380e"
down_revision: Union[str, Sequence[str], None] = "3571e1ef04d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "prediction_results",
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column("time", sa.DateTime(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["timeseries.analyses.id"],
        ),
        sa.PrimaryKeyConstraint("analysis_id", "time"),
        schema="timeseries",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("prediction_results", schema="timeseries")
