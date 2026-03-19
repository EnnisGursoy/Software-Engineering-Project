"""add user_id to employee model

Revision ID: 0676cbb1b7d8
Revises: 
Create Date: 2026-03-19 12:57:46.702866

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0676cbb1b7d8'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'employees',
        sa.Column('user_id', sa.Integer(), nullable=True)
    )

    op.create_foreign_key(
        'fk_employees_user_id',
        'employees',
        'users',
        ['user_id'],
        ['user_id']
    )

def downgrade() -> None:
    """Downgrade schema."""
    pass
