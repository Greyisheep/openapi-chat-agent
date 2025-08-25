"""Add workflow and workflow_step tables

Revision ID: workflow_tables_002
Revises: auth_config_001
Create Date: 2024-12-28 08:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'workflow_tables_002'
down_revision = 'auth_config_001'
depends_on = None


def upgrade() -> None:
    """Add workflow and workflow_step tables."""
    
    # Create workflows table
    op.create_table('workflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('conversation_id', sa.String(length=255), nullable=False, index=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='running'),
        sa.Column('total_execution_time', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create workflow_steps table
    op.create_table('workflow_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('step_name', sa.String(length=255), nullable=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('tools_used', sa.JSON(), nullable=True),
        sa.Column('execution_time', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('depends_on', sa.JSON(), nullable=True),
        sa.Column('pass_result_to', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Remove workflow and workflow_step tables."""
    op.drop_table('workflow_steps')
    op.drop_table('workflows')
