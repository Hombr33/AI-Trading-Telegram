"""add description field to symbol mappings

Revision ID: 2025_08_25_1200
Revises: 2025_08_24_2217
Create Date: 2025-08-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2025_08_25_1200'
down_revision = '2025_08_24_2217'
branch_labels = None
depends_on = None


def upgrade():
    """Add description field to symbol mappings table."""
    op.add_column('symbol_mappings', sa.Column('description', sa.String(255), nullable=True))


def downgrade():
    """Remove description field from symbol mappings table."""
    op.drop_column('symbol_mappings', 'description')