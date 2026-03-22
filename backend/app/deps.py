from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.session import UserSession
from app.services.jwt_service import verify_token
from app.services.encryption import decrypt
from app.services.odoo_client import OdooClient

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UserSession:
    try:
        payload = verify_token(credentials.credentials, expected_type="access")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(
        select(UserSession).where(UserSession.jwt_token == credentials.credentials)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found")

    return session


async def get_odoo_client(session: UserSession = Depends(get_current_user)) -> OdooClient:
    api_key = decrypt(session.odoo_api_key_encrypted)
    return OdooClient(
        url=session.odoo_url,
        db=session.odoo_db,
        uid=session.odoo_uid,
        api_key=api_key,
    )
