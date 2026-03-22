import json
import pytest
import pytest_asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from sqlalchemy import select

from app.models.email import Email, EmailSource, EmailStatus, EmailClassification
from app.models.ignore_rule import IgnoreRule, RuleField, MatchType
from app.models.po_draft import PODraft
from app.models.cache import VendorCache, ProductCache
from app.workers.email_processor import process_pending_emails


@pytest_asyncio.fixture
async def patch_worker_session(db_session, monkeypatch):
    """Patch async_session in email_processor to use the test DB session."""
    @asynccontextmanager
    async def mock_session():
        yield db_session

    monkeypatch.setattr("app.workers.email_processor.async_session", mock_session)
    return db_session


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
async def test_process_no_pending_emails(patch_worker_session):
    """Should return immediately with no pending emails."""
    await process_pending_emails({})


@pytest.mark.asyncio
async def test_process_ignores_matching_rule(patch_worker_session):
    """Emails matching ignore rules should be marked IGNORED."""
    db = patch_worker_session
    email = await _insert_email(db, sender="spam@junk.com", subject="Free stuff")

    rule = IgnoreRule(
        field=RuleField.DOMAIN, match_type=MatchType.EXACT,
        value="junk.com", user_id=42,
    )
    db.add(rule)
    await db.commit()

    await process_pending_emails({})

    await db.refresh(email)
    assert email.status == EmailStatus.IGNORED


@pytest.mark.asyncio
async def test_process_classifies_and_creates_draft(patch_worker_session):
    """PO-classified emails should get a draft created."""
    db = patch_worker_session
    email = await _insert_email(
        db,
        sender="vendor@acme.com",
        subject="Purchase Order Confirmation PO-2024-001",
        body="Order confirmed. Item: Widget A, Qty: 10, Price: $5.00 each. Total: $50.00",
    )

    vendor = VendorCache(
        odoo_id=10, name="Acme Corp",
        email="vendor@acme.com", email_domain="acme.com",
    )
    db.add(vendor)

    product = ProductCache(
        odoo_id=100, name="Widget A",
        default_code="WID-A",
    )
    db.add(product)
    await db.commit()

    await process_pending_emails({})

    await db.refresh(email)
    assert email.status == EmailStatus.REVIEWED
    assert email.classification == EmailClassification.PURCHASE_ORDER

    draft_result = await db.execute(select(PODraft))
    drafts = draft_result.scalars().all()
    assert len(drafts) == 1
    assert drafts[0].email_id == email.id
    assert drafts[0].vendor_name == "Acme Corp"


@pytest.mark.asyncio
async def test_process_unclassified_goes_to_triage(patch_worker_session):
    """Unclassified emails should go to TRIAGE for human review."""
    db = patch_worker_session
    email = await _insert_email(
        db,
        sender="random@example.com",
        subject="Hey there",
        body="Just wanted to say hello. Nothing about orders here.",
    )

    await process_pending_emails({})

    await db.refresh(email)
    assert email.status == EmailStatus.TRIAGE
    assert email.classification == EmailClassification.UNCLASSIFIED


@pytest.mark.asyncio
async def test_process_shipping_notice(patch_worker_session):
    """Shipping notices should be classified and marked REVIEWED."""
    db = patch_worker_session
    email = await _insert_email(
        db,
        sender="shipping@fedex.com",
        subject="Your shipment has been shipped - Tracking 1Z999AA10123456784",
        body="Your package has shipped via UPS. Tracking number: 1Z999AA10123456784. Estimated delivery: tomorrow.",
    )

    await process_pending_emails({})

    await db.refresh(email)
    assert email.status == EmailStatus.REVIEWED
    assert email.classification == EmailClassification.SHIPPING_NOTICE
