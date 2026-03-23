"""add external_id to emails for M365 dedup

Revision ID: 002
Revises: 001
Create Date: 2026-03-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("emails", sa.Column("external_id", sa.String(500), nullable=True))
    op.create_unique_constraint("uq_emails_external_id", "emails", ["external_id"])


def downgrade() -> None:
    op.drop_constraint("uq_emails_external_id", "emails", type_="unique")
    op.drop_column("emails", "external_id")
