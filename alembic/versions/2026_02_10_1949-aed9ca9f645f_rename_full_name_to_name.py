"""rename_full_name_to_name

Revision ID: aed9ca9f645f
Revises: a7549b2c335e
Create Date: 2026-02-10 19:49:09.693479

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aed9ca9f645f'
down_revision: Union[str, Sequence[str], None] = 'a7549b2c335e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('users', 'full_name', new_column_name='name')
    op.drop_index('idx_users_full_name', table_name='users')
    op.create_index('idx_users_name', 'users', ['name'])


def downgrade() -> None:
    op.alter_column('users', 'name', new_column_name='full_name')
    op.drop_index('idx_users_name', table_name='users')
    op.create_index('idx_users_full_name', 'users', ['full_name'])
