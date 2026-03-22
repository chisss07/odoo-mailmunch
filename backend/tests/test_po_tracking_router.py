import json
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from app.models.session import UserSession
from app.models.po_tracking import POTracking, POStatus
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
        refresh_token="fake-refresh-tracking",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        refresh_expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(session)
    await db_session.commit()
    return {"Authorization": f"Bearer {token}"}


async def _insert_tracking(db_session, status=POStatus.ordered):
    tracking = POTracking(
        odoo_po_id=100,
        odoo_po_name="PO00100",
        vendor_name="Acme Corp",
        status=status,
        user_id=42,
    )
    db_session.add(tracking)
    await db_session.commit()
    await db_session.refresh(tracking)
    return tracking


@pytest.mark.asyncio
async def test_list_pos_empty(client, db_session):
    headers = await _setup_auth(db_session)
    response = await client.get("/api/pos/", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_pos(client, db_session):
    headers = await _setup_auth(db_session)
    await _insert_tracking(db_session)
    response = await client.get("/api/pos/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["odoo_po_name"] == "PO00100"
    assert data[0]["status"] == "ordered"


@pytest.mark.asyncio
async def test_list_pos_filter_by_status(client, db_session):
    headers = await _setup_auth(db_session)
    await _insert_tracking(db_session, status=POStatus.ordered)
    await _insert_tracking(db_session, status=POStatus.received)
    response = await client.get("/api/pos/?status=ordered", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_po(client, db_session):
    headers = await _setup_auth(db_session)
    tracking = await _insert_tracking(db_session)
    response = await client.get(f"/api/pos/{tracking.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["odoo_po_id"] == 100
    assert data["last_synced"] is not None


@pytest.mark.asyncio
async def test_get_po_not_found(client, db_session):
    headers = await _setup_auth(db_session)
    response = await client.get("/api/pos/9999", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_receive_po_full(client, db_session):
    headers = await _setup_auth(db_session)
    tracking = await _insert_tracking(db_session)

    mock_receipt = {"picking_name": "WH/IN/00001"}
    with patch("app.routers.po_tracking.create_receipt_in_odoo", new_callable=AsyncMock, return_value=mock_receipt):
        response = await client.post(
            f"/api/pos/{tracking.id}/receive",
            json={},
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert data["picking_name"] == "WH/IN/00001"


@pytest.mark.asyncio
async def test_receive_po_partial(client, db_session):
    headers = await _setup_auth(db_session)
    tracking = await _insert_tracking(db_session)

    mock_receipt = {"picking_name": "WH/IN/00002"}
    partial_lines = [{"product_id": 1, "qty": 3}]
    with patch("app.routers.po_tracking.create_receipt_in_odoo", new_callable=AsyncMock, return_value=mock_receipt):
        response = await client.post(
            f"/api/pos/{tracking.id}/receive",
            json={"lines": partial_lines},
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "partial"
