import json
import pytest
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import Base, get_db
from app.models.email import Email, EmailSource, EmailStatus, EmailClassification
from app.models.ignore_rule import IgnoreRule, RuleField, MatchType
from app.models.po_draft import PODraft
from app.models.cache import VendorCache, ProductCache
from app.workers.email_processor import process_pending_emails


async def _insert_email(db, sender="vendor@acme.com", subject="Order Confirmation #123",
                        body="Widget A, Qty: 10, $5.00 each. Total: $50.00",
                        status=EmailStatus.PROCESSING):
    email = Email(
        sender=sender,
        sender_domain=sender.split("@")[-1] if "@" in sender else "",
        subject=subject,
        body_text=body,
        source=EmailSource.PASTE,
        status=status,
        classification=EmailClassification.UNCLASSIFIED,
        user_id=42,
    )
    db.add(email)
    await db.commit()
    await db.refresh(email)
    return email


@pytest.mark.asyncio
async def test_process_no_pending_emails(db_session, monkeypatch):
    """Should return immediately with no pending emails."""
    monkeypatch.setattr("app.workers.email_processor.async_session", lambda: db_session)

    # Patch context manager for async_session
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_session():
        yield db_session

    monkeypatch.setattr("app.workers.email_processor.async_session", mock_session)

    await process_pending_emails({})
    # No error means success


@pytest.mark.asyncio
async def test_process_ignores_matching_rule(db_session, monkeypatch):
    """Emails matching ignore rules should be marked IGNORED."""
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_session():
        yield db_session

    monkeypatch.setattr("app.workers.email_processor.async_session", mock_session)

    email = await _insert_email(db_session, sender="spam@junk.com", subject="Free stuff")

    rule = IgnoreRule(
        field=RuleField.DOMAIN, match_type=MatchType.EXACT,
        value="junk.com", user_id=42,
    )
    db_session.add(rule)
    await db_session.commit()

    await process_pending_emails({})

    await db_session.refresh(email)
    assert email.status == EmailStatus.IGNORED


@pytest.mark.asyncio
async def test_process_classifies_and_creates_draft(db_session, monkeypatch):
    """PO-classified emails should get a draft created."""
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_session():
        yield db_session

    monkeypatch.setattr("app.workers.email_processor.async_session", mock_session)

    email = await _insert_email(
        db_session,
        sender="vendor@acme.com",
        subject="Purchase Order Confirmation PO-2024-001",
        body="Order confirmed. Item: Widget A, Qty: 10, Price: $5.00 each. Total: $50.00",
    )

    # Add a vendor to cache for matching
    vendor = VendorCache(
        odoo_id=10, name="Acme Corp",
        email="vendor@acme.com", email_domain="acme.com",
    )
    db_session.add(vendor)

    # Add a product to cache for matching
    product = ProductCache(
        odoo_id=100, name="Widget A",
        default_code="WID-A",
    )
    db_session.add(product)
    await db_session.commit()

    await process_pending_emails({})

    await db_session.refresh(email)
    assert email.status == EmailStatus.REVIEWED
    assert email.classification == EmailClassification.PURCHASE_ORDER

    # Check draft was created
    draft_result = await db_session.execute(select(PODraft))
    drafts = draft_result.scalars().all()
    assert len(drafts) == 1
    assert drafts[0].email_id == email.id
    assert drafts[0].vendor_name == "Acme Corp"


@pytest.mark.asyncio
async def test_process_unclassified_goes_to_triage(db_session, monkeypatch):
    """Unclassified emails should go to TRIAGE for human review."""
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_session():
        yield db_session

    monkeypatch.setattr("app.workers.email_processor.async_session", mock_session)

    email = await _insert_email(
        db_session,
        sender="random@example.com",
        subject="Hey there",
        body="Just wanted to say hello. Nothing about orders here.",
    )

    await process_pending_emails({})

    await db_session.refresh(email)
    assert email.status == EmailStatus.TRIAGE
    assert email.classification == EmailClassification.UNCLASSIFIED


@pytest.mark.asyncio
async def test_process_shipping_notice(db_session, monkeypatch):
    """Shipping notices should be classified and marked REVIEWED."""
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_session():
        yield db_session

    monkeypatch.setattr("app.workers.email_processor.async_session", mock_session)

    email = await _insert_email(
        db_session,
        sender="shipping@fedex.com",
        subject="Your shipment has been shipped - Tracking 1Z999AA10123456784",
        body="Your package has shipped via UPS. Tracking number: 1Z999AA10123456784. Estimated delivery: tomorrow.",
    )

    await process_pending_emails({})

    await db_session.refresh(email)
    assert email.status == EmailStatus.REVIEWED
    assert email.classification == EmailClassification.SHIPPING_NOTICE
