"""Initial

Revision ID: a2a07af82d7b
Revises:
Create Date: 2025-12-01 13:21:45.958999

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a2a07af82d7b"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS timeseries")

    op.create_table(
        "datasets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="timeseries",
    )
    op.create_index(
        op.f("ix_timeseries_datasets_name"),
        "datasets",
        ["name"],
        unique=True,
        schema="timeseries",
    )

    op.create_table(
        "analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["dataset_id"], ["timeseries.datasets.id"]),
        sa.PrimaryKeyConstraint("id"),
        schema="timeseries",
    )
    op.create_index(
        op.f("ix_timeseries_analyses_dataset_id"),
        "analyses",
        ["dataset_id"],
        unique=False,
        schema="timeseries",
    )

    op.create_table(
        "datapoints",
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.Column("time", sa.DateTime(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["timeseries.datasets.id"]),
        sa.PrimaryKeyConstraint("dataset_id", "time"),
        schema="timeseries",
    )

    op.create_table(
        "anomalies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column("start", sa.DateTime(), nullable=False),
        sa.Column("end", sa.DateTime(), nullable=False),
        sa.Column("validated", sa.Boolean(), nullable=False),
        sa.Column("type", sa.Enum("point", "contextual", name="anomalytype"), nullable=True),
        sa.ForeignKeyConstraint(["analysis_id"], ["timeseries.analyses.id"]),
        sa.PrimaryKeyConstraint("id"),
        schema="timeseries",
    )
    op.create_index(
        op.f("ix_timeseries_anomalies_analysis_id"),
        "anomalies",
        ["analysis_id"],
        unique=False,
        schema="timeseries",
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_timeseries_anomalies_analysis_id"), table_name="anomalies", schema="timeseries")
    op.drop_table("anomalies", schema="timeseries")

    op.drop_table("datapoints", schema="timeseries")

    op.drop_index(op.f("ix_timeseries_analyses_dataset_id"), table_name="analyses", schema="timeseries")
    op.drop_table("analyses", schema="timeseries")

    op.drop_index(op.f("ix_timeseries_datasets_name"), table_name="datasets", schema="timeseries")
    op.drop_table("datasets", schema="timeseries")

    op.execute("DROP TYPE IF EXISTS timeseries.anomalytype;")
    # optional cleanup:
    # op.execute("DROP SCHEMA IF EXISTS timeseries;")
