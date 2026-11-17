"""create clinics and clinic_members

Revision ID: 0001
Revises:
Create Date: 2026-11-17
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("address", sa.String(255)),
        sa.Column("phone", sa.String(15)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "clinic_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.UniqueConstraint("clinic_id", "user_id", name="uq_clinic_user"),
    )
    op.create_index("ix_clinic_members_clinic_id", "clinic_members", ["clinic_id"])
    op.create_index("ix_clinic_members_user_id", "clinic_members", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_clinic_members_user_id", table_name="clinic_members")
    op.drop_index("ix_clinic_members_clinic_id", table_name="clinic_members")
    op.drop_table("clinic_members")
    op.drop_table("clinics")
