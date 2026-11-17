"""add clinic_id to doctors

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("doctors", sa.Column("clinic_id", sa.Integer(), nullable=True))
    op.create_index("ix_doctors_clinic_id", "doctors", ["clinic_id"])


def downgrade() -> None:
    op.drop_index("ix_doctors_clinic_id", table_name="doctors")
    op.drop_column("doctors", "clinic_id")
