"""outbox events and booking snapshots

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-18
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("appointments", sa.Column("patient_name", sa.String(100)))
    op.add_column("appointments", sa.Column("patient_email", sa.String(255)))
    op.add_column("appointments", sa.Column("doctor_name", sa.String(100)))

    op.create_table(
        "outbox_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.String(36), nullable=False, unique=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("published_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "ix_outbox_unpublished", "outbox_events", ["id"],
        postgresql_where=sa.text("published_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_unpublished", table_name="outbox_events")
    op.drop_table("outbox_events")
    op.drop_column("appointments", "doctor_name")
    op.drop_column("appointments", "patient_email")
    op.drop_column("appointments", "patient_name")
