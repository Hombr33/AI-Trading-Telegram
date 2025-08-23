"""add symbol mappings

Revision ID: f862e6ed7666
Revises: f862e6ed7665
Create Date: 2024-02-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f862e6ed7666'
down_revision = 'f862e6ed7665'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'symbol_mappings',
        sa.Column('standard_symbol', sa.String(20), nullable=False),
        sa.Column('broker_symbol', sa.String(20), nullable=False),
        sa.Column('broker_name', sa.String(50), nullable=False),
        sa.PrimaryKeyConstraint('standard_symbol', 'broker_name'),
        sa.UniqueConstraint('broker_name', 'broker_symbol', name='uix_broker_symbol')
    )


def downgrade():
    op.drop_table('symbol_mappings')
