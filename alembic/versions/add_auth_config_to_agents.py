"""Add auth configuration to agents

Revision ID: auth_config_001
Revises: 
Create Date: 2024-12-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'auth_config_001'
down_revision = None
depends_on = None


def upgrade() -> None:
    """Add auth configuration columns to agents table."""
    op.add_column('agents', sa.Column('auth_type', sa.String(length=50), nullable=False, server_default='bearer'))
    op.add_column('agents', sa.Column('auth_header', sa.String(length=100), nullable=False, server_default='Authorization'))
    op.add_column('agents', sa.Column('auth_prefix', sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Remove auth configuration columns from agents table."""
    op.drop_column('agents', 'auth_prefix')
    op.drop_column('agents', 'auth_header')
    op.drop_column('agents', 'auth_type')
