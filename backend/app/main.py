from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings


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

    # Mount SPA static files (built frontend) — only in production
    spa_path = Path("/app/frontend/dist")
    if spa_path.exists():
        app.mount("/", StaticFiles(directory=str(spa_path), html=True), name="spa")

    return app


app = create_app()
