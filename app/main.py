"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import calculate, health, rules
from app.config import settings
from app.exceptions.handlers import register_exception_handlers


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="""
        Nederlandse hypotheek maandlasten calculator.

        Berekent bruto en netto maandlasten inclusief:
        - Renteaftrek box 1 (met max aftrekpercentage)
        - Eigenwoningforfait (EWF)
        - Wet Hillen correctie
        - Partner verdeling (fixed percent, fixed amount, optimize)
        """,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Include routers
    app.include_router(health.router)
    app.include_router(calculate.router)
    app.include_router(rules.router)

    return app


app = create_app()
