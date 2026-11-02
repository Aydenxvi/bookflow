"""FastAPI application factory."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.routers import (
    admin_bookings,
    admin_business,
    admin_dashboard,
    admin_services,
    admin_staff,
    auth,
    availability,
    bookings,
    businesses,
)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(debug=settings.debug)

    app = FastAPI(title=settings.app_name, debug=settings.debug)

    # Regex is only applied outside production: it exists to tolerate the local-dev port
    # remapping docker-compose.yml already supports (WEB_PORT etc colliding with other
    # projects on the machine), not to loosen CORS once this is actually deployed.
    origin_regex = settings.cors_allow_origin_regex if settings.environment != "production" else None
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_origin_regex=origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(businesses.router)
    app.include_router(availability.router)
    app.include_router(bookings.router)
    app.include_router(admin_dashboard.router)
    app.include_router(admin_services.router)
    app.include_router(admin_staff.router)
    app.include_router(admin_business.router)
    app.include_router(admin_bookings.router)

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()
