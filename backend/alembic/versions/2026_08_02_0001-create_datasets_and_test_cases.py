"""create datasets and test_cases tables

Revision ID: 2026_08_02_0001
Revises: 
Create Date: 2026-08-02 18:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2026_08_02_0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'datasets',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table(
        'test_cases',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('dataset_id', sa.String(length=64), nullable=False),
        sa.Column('input', sa.Text(), nullable=False),
        sa.Column('expected_output', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('metadata_json', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_test_cases_dataset_id', 'test_cases', ['dataset_id'], unique=False)
    op.create_index('idx_test_cases_category', 'test_cases', ['category'], unique=False)

def downgrade() -> None:
    op.drop_index('idx_test_cases_category', table_name='test_cases')
    op.drop_index('idx_test_cases_dataset_id', table_name='test_cases')
    op.drop_table('test_cases')
    op.drop_table('datasets')
