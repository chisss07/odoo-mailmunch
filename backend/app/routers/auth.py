from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models.session import UserSession
from app.services.encryption import encrypt
from app.services.jwt_service import create_access_token, create_refresh_token, verify_token
from app.services.odoo_auth import authenticate_odoo

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    odoo_url: str
    database: str
    email: str
    api_key: str | None = None
    password: str | None = None

    def get_credential(self) -> str:
        if self.api_key and self.password:
            raise ValueError("Provide either api_key or password, not both")
        credential = self.api_key or self.password
        if not credential:
            raise ValueError("Either api_key or password is required")
        return credential


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        credential = req.get_credential()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    try:
        result = await authenticate_odoo(
            req.odoo_url, req.database, req.email, credential,
            is_api_key=req.api_key is not None,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    uid = result["uid"]
    access_token = create_access_token(user_id=uid, odoo_uid=uid, odoo_url=req.odoo_url)
    refresh_token = create_refresh_token(user_id=uid)

    session = UserSession(
        user_id=uid,
        odoo_uid=uid,
        odoo_url=req.odoo_url,
        odoo_db=req.database,
        odoo_api_key_encrypted=encrypt(credential),
        jwt_token=access_token,
        refresh_token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiry_minutes),
        refresh_expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expiry_days),
    )
    db.add(session)
    await db.commit()

    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/refresh")
async def refresh(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        verify_token(req.refresh_token, expected_type="refresh")
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

    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/logout")
async def logout(
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.delete(current_user)
    await db.commit()
    return {"status": "ok"}


@router.get("/session")
async def get_session(current_user: UserSession = Depends(get_current_user)):
    return {"odoo_url": current_user.odoo_url, "database": current_user.odoo_db}
