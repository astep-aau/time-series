"""Create timeseries schema

Revision ID: fa61e0cbfae7
Revises:
Create Date: 2025-12-01 11:15:14.537242

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "fa61e0cbfae7"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
