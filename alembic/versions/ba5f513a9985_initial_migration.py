"""Обновление схем

Revision ID: ba5f513a9985
Revises: bd8d32e1a187
Create Date: 2025-03-01 07:01:08.868153

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba5f513a9985'
down_revision: Union[str, None] = 'bd8d32e1a187'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'reservations',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('seat_id', sa.UUID(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('reservations')