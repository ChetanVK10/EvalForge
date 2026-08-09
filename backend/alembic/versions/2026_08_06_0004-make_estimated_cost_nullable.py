"""make experiments.estimated_cost nullable

Revision ID: 2026_08_06_0004
Revises: 2026_08_02_0003
Create Date: 2026-08-06 05:00:00.000000

The experiments.estimated_cost column was originally created with
nullable=False, server_default='0.0'. This conflicts with the intended
semantics where:
  - A pending experiment has no cost yet (should be NULL, not 0.0).
  - A completed experiment using an unpriced/unknown model should also
    remain NULL so the frontend can display "N/A" rather than a misleading $0.00.

The SQLAlchemy model already declared nullable=True. This migration aligns
the PostgreSQL schema with the model by:
  1. Dropping the server_default='0.0'.
  2. Altering the column to nullable=True (dropping the NOT NULL constraint).

Existing rows with estimated_cost=0.0 are preserved as-is; only the
schema constraint is changed.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2026_08_06_0004'
down_revision: Union[str, None] = '2026_08_02_0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the server default first, then relax the NOT NULL constraint.
    # Two separate alter_column calls because some DB backends need them separated,
    # but a single call works correctly on PostgreSQL via psycopg/SQLAlchemy.
    with op.batch_alter_table('experiments', schema=None) as batch_op:
        batch_op.alter_column(
            'estimated_cost',
            existing_type=sa.Float(),
            nullable=True,
            server_default=None,  # remove the '0.0' server default
        )


def downgrade() -> None:
    # Restore original: fill NULLs with 0.0 first to avoid violating the constraint on downgrade.
    op.execute(
        "UPDATE experiments SET estimated_cost = 0.0 WHERE estimated_cost IS NULL"
    )
    with op.batch_alter_table('experiments', schema=None) as batch_op:
        batch_op.alter_column(
            'estimated_cost',
            existing_type=sa.Float(),
            nullable=False,
            server_default='0.0',
        )
