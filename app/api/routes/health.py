"""Health and version endpoints."""

from fastapi import APIRouter

from app.config import settings
from app.rules.loader import get_available_years

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    description="Check if the service is running and healthy",
)
async def health_check():
    """Return health status."""
    return {
        "status": "healthy",
        "service": settings.app_name,
    }


@router.get(
    "/version",
    summary="Version info",
    description="Get service version and available fiscal years",
)
async def version_info():
    """Return version information."""
    return {
        "version": settings.app_version,
        "service": settings.app_name,
        "available_fiscal_years": get_available_years(),
    }
