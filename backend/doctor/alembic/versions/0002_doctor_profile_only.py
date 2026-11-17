"""doctors become profiles linked to the auth service

Identity (email, username, password) moved to the auth service. This
migration is NON-destructive: legacy columns are kept but made optional, so
no data is lost. Drop them in a later migration once you no longer need them.

Legacy rows have no user_id. They are unreachable through the API; clear them
(dev) or backfill user_id before relying on them.

Revision ID: 0002
Revises: 8dd3ce4fc065
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "8dd3ce4fc065"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("doctors", sa.Column("user_id", sa.Integer(), nullable=True))
    op.add_column("doctors", sa.Column("full_name", sa.String(100), nullable=True))
    op.add_column("doctors", sa.Column("specialty", sa.String(100), nullable=True))
    op.create_index("ix_doctors_user_id", "doctors", ["user_id"], unique=True)

    for column in ("username", "email", "password"):
        op.alter_column("doctors", column, nullable=True)


def downgrade() -> None:
    # Re-adding NOT NULL fails if profile-only rows exist; that is intended.
    for column in ("username", "email", "password"):
        op.alter_column("doctors", column, nullable=False)
    op.drop_index("ix_doctors_user_id", table_name="doctors")
    op.drop_column("doctors", "specialty")
    op.drop_column("doctors", "full_name")
    op.drop_column("doctors", "user_id")
