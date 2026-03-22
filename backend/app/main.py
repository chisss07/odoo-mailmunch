from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.routers import auth as auth_router


def create_app() -> FastAPI:
    app = FastAPI(title="Odoo-MailMunch", version="0.1.0")

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

    # NOTE: All API routers must be included ABOVE this line.
    # The SPA static file mount catches ALL unmatched routes.
    # Any router registered after this mount will be unreachable.
    spa_path = Path("/app/frontend/dist")
    if spa_path.exists():
        app.mount("/", StaticFiles(directory=str(spa_path), html=True), name="spa")

    return app


app = create_app()
