import json
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from app.models.session import UserSession
from app.models.po_draft import PODraft, DraftStatus
from app.models.po_tracking import POTracking
from app.services.encryption import encrypt
from app.services.jwt_service import create_access_token
from sqlalchemy import select


async def _setup_auth(db_session):
    token = create_access_token(user_id=1, odoo_uid=42, odoo_url="https://test.odoo.com")
    session = UserSession(
        user_id=1,
        odoo_uid=42,
        odoo_url="https://test.odoo.com",
        odoo_db="testdb",
        odoo_session_encrypted=encrypt("fake-session"),
        jwt_token=token,
        refresh_token="fake-refresh-drafts",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        refresh_expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(session)
    await db_session.commit()
    return {"Authorization": f"Bearer {token}"}


async def _insert_draft(db_session, vendor_odoo_id=10, line_items=None, status=DraftStatus.DRAFT):
    if line_items is None:
        line_items = [{"product_id": 1, "name": "Widget A", "qty": 5, "price": 10.0}]
    draft = PODraft(
        email_id=1,
        vendor_odoo_id=vendor_odoo_id,
        vendor_name="Acme Corp",
        line_items=json.dumps(line_items),
        total_amount="50.00",
        user_id=42,
        status=status,
    )
    db_session.add(draft)
    await db_session.commit()
    await db_session.refresh(draft)
    return draft


@pytest.mark.asyncio
async def test_list_drafts_empty(client, db_session):
    headers = await _setup_auth(db_session)
    response = await client.get("/api/drafts/", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_drafts_excludes_submitted(client, db_session):
    headers = await _setup_auth(db_session)
    await _insert_draft(db_session, status=DraftStatus.DRAFT)
    await _insert_draft(db_session, status=DraftStatus.SUBMITTED)
    response = await client.get("/api/drafts/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_draft(client, db_session):
    headers = await _setup_auth(db_session)
    draft = await _insert_draft(db_session)
    response = await client.get(f"/api/drafts/{draft.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["vendor_name"] == "Acme Corp"
    assert len(data["line_items"]) == 1


@pytest.mark.asyncio
async def test_get_draft_not_found(client, db_session):
    headers = await _setup_auth(db_session)
    response = await client.get("/api/drafts/9999", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_draft(client, db_session):
    headers = await _setup_auth(db_session)
    draft = await _insert_draft(db_session)
    response = await client.put(
        f"/api/drafts/{draft.id}",
        json={"vendor_name": "New Corp"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "updated"


@pytest.mark.asyncio
async def test_submit_draft_missing_vendor(client, db_session):
    headers = await _setup_auth(db_session)
    draft = await _insert_draft(db_session, vendor_odoo_id=None)
    response = await client.post(f"/api/drafts/{draft.id}/submit", headers=headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_submit_draft_success(client, db_session):
    headers = await _setup_auth(db_session)
    draft = await _insert_draft(db_session)

    mock_result = {"id": 100, "name": "PO00100"}
    with patch("app.routers.po_drafts.create_po_in_odoo", new_callable=AsyncMock, return_value=mock_result):
        response = await client.post(f"/api/drafts/{draft.id}/submit", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["po_id"] == 100
    assert data["po_name"] == "PO00100"

    # Verify tracking record was created with correct enum status
    result = await db_session.execute(select(POTracking))
    tracking = result.scalars().all()
    assert len(tracking) == 1
    assert tracking[0].status.value == "ordered"
    assert tracking[0].odoo_po_id == 100
