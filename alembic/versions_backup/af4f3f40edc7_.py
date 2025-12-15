"""empty message

Revision ID: af4f3f40edc7
Revises: 3571e1ef04d0, ab4fd44eb440
Create Date: 2025-12-15 15:47:35.499972

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "af4f3f40edc7"
down_revision: Union[str, Sequence[str], None] = ("3571e1ef04d0", "ab4fd44eb440")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
