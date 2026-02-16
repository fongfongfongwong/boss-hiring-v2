"""FastAPI application factory."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database.db import init_db
from web.routes import boss_accounts, candidates, dashboard, market_research, positions, settings, tasks, websocket


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Boss 直聘自动化招聘系统",
        version="1.0.0",
        description="Automated recruitment system powered by RPA + LLM",
    )

    # CORS – allow frontend dev server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routes
    app.include_router(positions.router)
    app.include_router(tasks.router)
    app.include_router(candidates.router)
    app.include_router(dashboard.router)
    app.include_router(settings.router)
    app.include_router(boss_accounts.router)
    app.include_router(market_research.router)
    app.include_router(websocket.router)

    # Serve frontend build (if exists)
    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    # Initialize database on startup
    @app.on_event("startup")
    def on_startup() -> None:
        init_db()

    @app.get("/api/health")
    def health_check():
        return {"status": "ok"}

    return app
