"""patients belong to clinics

doctor_id (the owning doctor) becomes created_by_user_id (audit only);
clinic_id becomes the ownership key. Non-destructive: legacy rows keep their
data but have clinic_id NULL, so they are unreachable through the API until
you backfill clinic_id or delete them (dev).

Revision ID: 0002
Revises: b50f5ea6e0b5
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "b50f5ea6e0b5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("patients", sa.Column("clinic_id", sa.Integer(), nullable=True))
    op.create_index("ix_patients_clinic_id", "patients", ["clinic_id"])

    op.drop_index("ix_patients_doctor_id", table_name="patients")
    op.alter_column("patients", "doctor_id", new_column_name="created_by_user_id")
    op.create_index("ix_patients_created_by_user_id", "patients", ["created_by_user_id"])


def downgrade() -> None:
    op.drop_index("ix_patients_created_by_user_id", table_name="patients")
    op.alter_column("patients", "created_by_user_id", new_column_name="doctor_id")
    op.create_index("ix_patients_doctor_id", "patients", ["doctor_id"])

    op.drop_index("ix_patients_clinic_id", table_name="patients")
    op.drop_column("patients", "clinic_id")
