"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # sessions
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("odoo_uid", sa.Integer(), nullable=False),
        sa.Column("odoo_url", sa.String(500), nullable=False),
        sa.Column("odoo_db", sa.String(200), nullable=False),
        sa.Column("odoo_session_encrypted", sa.Text(), nullable=False),
        sa.Column("jwt_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("refresh_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jwt_token"),
        sa.UniqueConstraint("refresh_token"),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_jwt_token", "sessions", ["jwt_token"])
    op.create_index("ix_sessions_refresh_token", "sessions", ["refresh_token"])

    # emails
    op.create_table(
        "emails",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sender", sa.String(500), nullable=False),
        sa.Column("sender_domain", sa.String(250), nullable=False),
        sa.Column("subject", sa.String(1000), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("attachment_paths", sa.Text(), nullable=True),
        sa.Column(
            "source",
            sa.Enum("m365", "forward", "upload", "paste", name="emailsource"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("triage", "processing", "reviewed", "ignored", name="emailstatus"),
            nullable=False,
        ),
        sa.Column(
            "classification",
            sa.Enum(
                "purchase_order", "shipping_notice", "bill", "unrelated", "unclassified",
                name="emailclassification",
            ),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_emails_sender_domain", "emails", ["sender_domain"])
    op.create_index("ix_emails_status", "emails", ["status"])
    op.create_index("ix_emails_user_id", "emails", ["user_id"])

    # ignore_rules
    op.create_table(
        "ignore_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "field",
            sa.Enum("sender", "domain", "subject", name="rulefield"),
            nullable=False,
        ),
        sa.Column(
            "match_type",
            sa.Enum("exact", "contains", "regex", name="matchtype"),
            nullable=False,
        ),
        sa.Column("value", sa.String(500), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ignore_rules_user_id", "ignore_rules", ["user_id"])

    # po_drafts
    op.create_table(
        "po_drafts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email_id", sa.Integer(), nullable=False),
        sa.Column("vendor_odoo_id", sa.Integer(), nullable=True),
        sa.Column("vendor_name", sa.String(500), nullable=False),
        sa.Column("vendor_confidence", sa.String(10), nullable=False),
        sa.Column("line_items", sa.Text(), nullable=False),
        sa.Column("total_amount", sa.String(50), nullable=True),
        sa.Column("expected_date", sa.String(50), nullable=True),
        sa.Column("sales_order_id", sa.Integer(), nullable=True),
        sa.Column("sales_order_name", sa.String(100), nullable=True),
        sa.Column(
            "status",
            sa.Enum("draft", "submitted", name="draftstatus"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_po_drafts_email_id", "po_drafts", ["email_id"])
    op.create_index("ix_po_drafts_user_id", "po_drafts", ["user_id"])

    # po_tracking
    op.create_table(
        "po_tracking",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("odoo_po_id", sa.Integer(), nullable=False),
        sa.Column("odoo_po_name", sa.String(100), nullable=False),
        sa.Column("vendor_name", sa.String(500), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("sales_order_id", sa.Integer(), nullable=True),
        sa.Column("sales_order_name", sa.String(100), nullable=True),
        sa.Column("tracking_info", sa.Text(), nullable=True),
        sa.Column("draft_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("last_synced", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_po_tracking_odoo_po_id", "po_tracking", ["odoo_po_id"])
    op.create_index("ix_po_tracking_status", "po_tracking", ["status"])
    op.create_index("ix_po_tracking_user_id", "po_tracking", ["user_id"])

    # product_cache
    op.create_table(
        "product_cache",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("odoo_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("default_code", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("last_refreshed", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("odoo_id"),
    )
    op.create_index("ix_product_cache_odoo_id", "product_cache", ["odoo_id"])
    op.create_index("ix_product_cache_default_code", "product_cache", ["default_code"])

    # vendor_cache
    op.create_table(
        "vendor_cache",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("odoo_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("email", sa.String(500), nullable=True),
        sa.Column("email_domain", sa.String(250), nullable=True),
        sa.Column("last_refreshed", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("odoo_id"),
    )
    op.create_index("ix_vendor_cache_odoo_id", "vendor_cache", ["odoo_id"])
    op.create_index("ix_vendor_cache_email_domain", "vendor_cache", ["email_domain"])

    # vendor_product_map
    op.create_table(
        "vendor_product_map",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vendor_odoo_id", sa.Integer(), nullable=False),
        sa.Column("product_odoo_id", sa.Integer(), nullable=False),
        sa.Column("vendor_price", sa.String(50), nullable=True),
        sa.Column("vendor_product_code", sa.String(100), nullable=True),
        sa.Column("last_refreshed", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vendor_product_map_vendor_odoo_id", "vendor_product_map", ["vendor_odoo_id"])
    op.create_index("ix_vendor_product_map_product_odoo_id", "vendor_product_map", ["product_odoo_id"])

    # settings
    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value_encrypted", sa.Text(), nullable=True),
        sa.Column("value_plain", sa.Text(), nullable=True),
        sa.Column("is_secret", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index("ix_settings_key", "settings", ["key"])


def downgrade() -> None:
    op.drop_table("settings")
    op.drop_table("vendor_product_map")
    op.drop_table("vendor_cache")
    op.drop_table("product_cache")
    op.drop_table("po_tracking")
    op.drop_table("po_drafts")
    op.drop_table("ignore_rules")
    op.drop_table("emails")
    op.drop_table("sessions")
    # Drop PostgreSQL enum types (no-op on SQLite)
    op.execute("DROP TYPE IF EXISTS emailstatus")
    op.execute("DROP TYPE IF EXISTS emailsource")
    op.execute("DROP TYPE IF EXISTS emailclassification")
    op.execute("DROP TYPE IF EXISTS rulefield")
    op.execute("DROP TYPE IF EXISTS matchtype")
    op.execute("DROP TYPE IF EXISTS draftstatus")
