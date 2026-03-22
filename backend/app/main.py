import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.database import engine, Base
from app.routers import auth as auth_router
from app.routers import emails as emails_router
from app.routers import triage as triage_router
from app.routers import po_drafts as po_drafts_router
from app.routers import po_tracking as po_tracking_router
from app.routers import odoo_proxy as odoo_proxy_router
from app.routers import settings as settings_router

# Import all models so Base.metadata knows about them
import app.models.session  # noqa: F401
import app.models.email  # noqa: F401
import app.models.ignore_rule  # noqa: F401
import app.models.po_draft  # noqa: F401
import app.models.po_tracking  # noqa: F401
import app.models.cache  # noqa: F401
import app.models.settings  # noqa: F401

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Odoo-MailMunch", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    app.include_router(auth_router.router)
    app.include_router(emails_router.router)
    app.include_router(triage_router.router)
    app.include_router(po_drafts_router.router)
    app.include_router(po_tracking_router.router)
    app.include_router(odoo_proxy_router.router)
    app.include_router(settings_router.router)

    # NOTE: All API routers must be included ABOVE this line.
    # The SPA static file mount catches ALL unmatched routes.
    # Any router registered after this mount will be unreachable.
    spa_path = Path("/app/frontend/dist")
    if spa_path.exists():
        app.mount("/", StaticFiles(directory=str(spa_path), html=True), name="spa")

    return app


app = create_app()
