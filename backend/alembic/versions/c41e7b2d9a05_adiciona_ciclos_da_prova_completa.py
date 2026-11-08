"""adiciona ciclos da prova completa

Revision ID: c41e7b2d9a05
Revises: 8474d8c39620
Create Date: 2026-11-07 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c41e7b2d9a05'
down_revision: Union[str, Sequence[str], None] = '8474d8c39620'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Coluna nula: registros antigos não têm os ciclos da prova completa
    # (o SWOLF deles fica vazio até o treino ser editado). A API exige o campo
    # em todo registro novo ou editado.
    op.add_column(
        'training_sessions',
        sa.Column('total_cycle_count', sa.Integer(), nullable=True),
    )
    op.create_check_constraint(
        'ck_total_cycle_count_positive',
        'training_sessions',
        'total_cycle_count IS NULL OR total_cycle_count >= 1',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'ck_total_cycle_count_positive', 'training_sessions', type_='check'
    )
    op.drop_column('training_sessions', 'total_cycle_count')