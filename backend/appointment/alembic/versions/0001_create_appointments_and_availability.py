"""create appointments and availability

Revision ID: 0001
Revises:
Create Date: 2026-11-18
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clinic_id", sa.Integer(), nullable=False),
        sa.Column("doctor_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reason", sa.String(255)),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(64)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("cancelled_by_user_id", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("created_by_user_id", "idempotency_key", name="uq_idempotency"),
    )
    op.create_index("ix_appointments_clinic_id", "appointments", ["clinic_id"])
    op.create_index("ix_appointments_doctor_id", "appointments", ["doctor_id"])
    op.create_index("ix_appointments_patient_id", "appointments", ["patient_id"])
    op.create_index("ix_appointments_starts_at", "appointments", ["starts_at"])

    # The double-booking guarantee (partial unique indexes: only 'booked' rows count).
    where = sa.text("status = 'booked'")
    op.create_index("uq_booked_doctor_slot", "appointments", ["doctor_id", "starts_at"],
                    unique=True, postgresql_where=where)
    op.create_index("uq_booked_patient_slot", "appointments", ["patient_id", "starts_at"],
                    unique=True, postgresql_where=where)

    op.create_table(
        "availability",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("doctor_id", sa.Integer(), nullable=False),
        sa.Column("clinic_id", sa.Integer(), nullable=False),
        sa.Column("weekday", sa.SmallInteger(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.UniqueConstraint("doctor_id", "weekday", "start_time", name="uq_doctor_window"),
    )
    op.create_index("ix_availability_doctor_id", "availability", ["doctor_id"])


def downgrade() -> None:
    op.drop_index("ix_availability_doctor_id", table_name="availability")
    op.drop_table("availability")
    op.drop_index("uq_booked_patient_slot", table_name="appointments")
    op.drop_index("uq_booked_doctor_slot", table_name="appointments")
    op.drop_index("ix_appointments_starts_at", table_name="appointments")
    op.drop_index("ix_appointments_patient_id", table_name="appointments")
    op.drop_index("ix_appointments_doctor_id", table_name="appointments")
    op.drop_index("ix_appointments_clinic_id", table_name="appointments")
    op.drop_table("appointments")
