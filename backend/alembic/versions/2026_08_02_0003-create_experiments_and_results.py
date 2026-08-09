"""create experiments, test_case_results, and evaluation_scores tables

Revision ID: 2026_08_02_0003
Revises: 2026_08_02_0002
Create Date: 2026-08-02 19:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2026_08_02_0003'
down_revision: Union[str, None] = '2026_08_02_0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. experiments table
    op.create_table(
        'experiments',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('dataset_id', sa.String(length=64), nullable=False),
        sa.Column('model_config_id', sa.String(length=64), nullable=False),
        sa.Column('prompt_id', sa.String(length=64), nullable=False),
        sa.Column('prompt_version_id', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('total_cases', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_cases', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_cases', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('pass_rate', sa.Float(), nullable=True),
        sa.Column('avg_latency_ms', sa.Integer(), nullable=True),
        sa.Column('p95_latency_ms', sa.Integer(), nullable=True),
        sa.Column('total_input_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_output_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('estimated_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('metrics_json', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
        sa.Column('snapshots_json', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id']),
        sa.ForeignKeyConstraint(['model_config_id'], ['model_configs.id']),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id']),
        sa.ForeignKeyConstraint(['prompt_version_id'], ['prompt_versions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_experiments_status', 'experiments', ['status'], unique=False)
    op.create_index('idx_experiments_created_at', 'experiments', ['created_at'], unique=False)

    # 2. test_case_results table
    op.create_table(
        'test_case_results',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('experiment_id', sa.String(length=64), nullable=False),
        sa.Column('test_case_id', sa.String(length=64), nullable=True),
        sa.Column('input', sa.Text(), nullable=False),
        sa.Column('expected_output', sa.Text(), nullable=False),
        sa.Column('model_output', sa.Text(), nullable=False, server_default=''),
        sa.Column('category', sa.String(length=64), nullable=False, server_default='general'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='completed'),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('provider', sa.String(length=32), nullable=False),
        sa.Column('model', sa.String(length=128), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('estimated_cost', sa.Float(), nullable=True),
        sa.Column('case_quality_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_test_case_results_experiment_id', 'test_case_results', ['experiment_id'], unique=False)
    op.create_index('idx_test_case_results_category', 'test_case_results', ['category'], unique=False)

    # 3. evaluation_scores table
    op.create_table(
        'evaluation_scores',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('test_case_result_id', sa.String(length=64), nullable=False),
        sa.Column('metric', sa.String(length=64), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='success'),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('details_json', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['test_case_result_id'], ['test_case_results.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_evaluation_scores_result_id', 'evaluation_scores', ['test_case_result_id'], unique=False)
    op.create_index('idx_evaluation_scores_metric', 'evaluation_scores', ['metric'], unique=False)

def downgrade() -> None:
    op.drop_index('idx_evaluation_scores_metric', table_name='evaluation_scores')
    op.drop_index('idx_evaluation_scores_result_id', table_name='evaluation_scores')
    op.drop_table('evaluation_scores')

    op.drop_index('idx_test_case_results_category', table_name='test_case_results')
    op.drop_index('idx_test_case_results_experiment_id', table_name='test_case_results')
    op.drop_table('test_case_results')

    op.drop_index('idx_experiments_created_at', table_name='experiments')
    op.drop_index('idx_experiments_status', table_name='experiments')
    op.drop_table('experiments')
