"""Add kakao social login fields to users

Revision ID: 001
Revises:
Create Date: 2026-05-07

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('users', 'password_hash',
               existing_type=sa.String(),
               nullable=True)
    op.add_column('users', sa.Column('provider', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('social_id', sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'social_id')
    op.drop_column('users', 'provider')
    op.alter_column('users', 'password_hash',
               existing_type=sa.String(),
               nullable=False)
