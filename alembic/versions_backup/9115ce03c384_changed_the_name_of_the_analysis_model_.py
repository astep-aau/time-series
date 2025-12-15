"""Changed the name of the analysis.model column to detection_method

Revision ID: 9115ce03c384
Revises: f6fbdc23912f
Create Date: 2025-12-03 14:15:10.186222

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9115ce03c384"
down_revision: Union[str, Sequence[str], None] = "f6fbdc23912f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("analyses", "model", new_column_name="detection_method")
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("analyses", "detection_method", new_column_name="model")
    # ### end Alembic commands ###
