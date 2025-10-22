"""rename tables to plural form

Revision ID: e54dea3e1c41
Revises: 47a2b1597a87
Create Date: 2025-10-22 16:22:54.509872

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "e54dea3e1c41"
down_revision: Union[str, Sequence[str], None] = "47a2b1597a87"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
