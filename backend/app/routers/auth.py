import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models.session import UserSession
from app.services.encryption import encrypt, decrypt
from app.services.jwt_service import create_access_token, create_refresh_token, verify_token
from app.services.odoo_auth import authenticate_odoo, verify_totp

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    odoo_url: str
    database: str
    email: str
    password: str


class TOTPRequest(BaseModel):
    totp_session: str
    totp_code: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await authenticate_odoo(req.odoo_url, req.database, req.email, req.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    if result["needs_totp"]:
        totp_data = json.dumps({
            "uid": result["uid"],
            "session_id": result["session_id"],
            "odoo_url": req.odoo_url,
            "database": req.database,
        })
        totp_session = encrypt(totp_data)
        return {"needs_totp": True, "totp_session": totp_session}

    return await _create_session(db, result["uid"], result["session_id"], req.odoo_url, req.database)


@router.post("/totp")
async def complete_totp(req: TOTPRequest, db: AsyncSession = Depends(get_db)):
    try:
        plain = decrypt(req.totp_session)
        totp_data = json.loads(plain)
        uid_str = str(totp_data["uid"])
        session_id = totp_data["session_id"]
        odoo_url = totp_data["odoo_url"]
        odoo_db = totp_data["database"]
        uid = int(uid_str)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP session")

    try:
        totp_result = await verify_totp(odoo_url, session_id, req.totp_code)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return await _create_session(db, uid, totp_result["session_id"], odoo_url, odoo_db)


@router.post("/refresh")
async def refresh(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = verify_token(req.refresh_token, expected_type="refresh")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await db.execute(
        select(UserSession).where(UserSession.refresh_token == req.refresh_token)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found")

    access_token = create_access_token(user_id=session.id, odoo_uid=session.odoo_uid, odoo_url=session.odoo_url)
    refresh_token = create_refresh_token(user_id=session.id)

    session.jwt_token = access_token
    session.refresh_token = refresh_token
    session.expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiry_minutes)
    session.refresh_expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expiry_days)

    await db.commit()

    return {"access_token": access_token, "refresh_token": refresh_token, "needs_totp": False}


@router.post("/logout")
async def logout(
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.delete(current_user)
    await db.commit()
    return {"status": "ok"}


async def _create_session(db: AsyncSession, uid: int, session_id: str, odoo_url: str, odoo_db: str) -> dict:
    access_token = create_access_token(user_id=uid, odoo_uid=uid, odoo_url=odoo_url)
    refresh_token = create_refresh_token(user_id=uid)

    session = UserSession(
        user_id=uid,
        odoo_uid=uid,
        odoo_url=odoo_url,
        odoo_db=odoo_db,
        odoo_session_encrypted=encrypt(session_id),
        jwt_token=access_token,
        refresh_token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiry_minutes),
        refresh_expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expiry_days),
    )
    db.add(session)
    await db.commit()

    return {"access_token": access_token, "refresh_token": refresh_token, "needs_totp": False}
