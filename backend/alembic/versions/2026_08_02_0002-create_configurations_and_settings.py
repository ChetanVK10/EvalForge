"""create model_configs, prompts, prompt_versions, and workspace_settings tables

Revision ID: 2026_08_02_0002
Revises: 2026_08_02_0001
Create Date: 2026-08-02 18:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2026_08_02_0002'
down_revision: Union[str, None] = '2026_08_02_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. model_configs table
    op.create_table(
        'model_configs',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('provider', sa.String(length=32), nullable=False),
        sa.Column('model', sa.String(length=128), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=False, server_default='0.2'),
        sa.Column('max_tokens', sa.Integer(), nullable=False, server_default='1024'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. prompts table
    op.create_table(
        'prompts',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. prompt_versions table
    op.create_table(
        'prompt_versions',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('prompt_id', sa.String(length=64), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('user_template', sa.Text(), nullable=False, server_default='{{input}}'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('prompt_id', 'version', name='uq_prompt_version')
    )
    op.create_index('idx_prompt_versions_prompt_id', 'prompt_versions', ['prompt_id'], unique=False)

    # 4. workspace_settings table
    op.create_table(
        'workspace_settings',
        sa.Column('id', sa.String(length=64), nullable=False, server_default='default'),
        sa.Column('evaluation_defaults_json', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
        sa.Column('regression_thresholds_json', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('workspace_settings')
    op.drop_index('idx_prompt_versions_prompt_id', table_name='prompt_versions')
    op.drop_table('prompt_versions')
    op.drop_table('prompts')
    op.drop_table('model_configs')
