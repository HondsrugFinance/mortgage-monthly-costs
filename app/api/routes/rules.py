"""Fiscal rules management endpoints."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.schemas.rules import FiscalRules
from app.exceptions import FiscalRulesNotFoundError, InvalidFiscalRulesError
from app.rules.loader import get_available_years, load_rules, save_rules
from app.rules.validator import validate_rules

router = APIRouter(prefix="/rules", tags=["rules"])


class ValidationResponse(BaseModel):
    """Response for rules validation."""

    valid: bool
    errors: list[str]
    warnings: list[str]


class UploadResponse(BaseModel):
    """Response for rules upload."""

    success: bool
    fiscal_year: int
    message: str


@router.get(
    "",
    summary="List available fiscal years",
    description="Get a list of all fiscal years for which rules are available",
)
async def list_available_years() -> dict[str, list[int]]:
    """List all available fiscal years."""
    return {"available_years": get_available_years()}


@router.get(
    "/{year}",
    response_model=FiscalRules,
    summary="Get fiscal rules for a year",
    description="Retrieve the complete fiscal rules configuration for a specific year",
)
async def get_rules(year: int) -> FiscalRules:
    """
    Get fiscal rules for a specific year.

    Args:
        year: The fiscal year to retrieve rules for

    Returns:
        Complete fiscal rules for the year

    Raises:
        HTTPException: If rules not found for the year
    """
    try:
        return load_rules(year)
    except FiscalRulesNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": e.error_code, "message": e.message},
        )


@router.post(
    "/{year}/validate",
    response_model=ValidationResponse,
    summary="Validate fiscal rules",
    description="Validate fiscal rules without saving them",
)
async def validate_rules_endpoint(year: int, rules: FiscalRules) -> ValidationResponse:
    """
    Validate fiscal rules for consistency.

    Args:
        year: The fiscal year (must match rules.fiscal_year)
        rules: The rules to validate

    Returns:
        Validation result with errors and warnings
    """
    if rules.fiscal_year != year:
        return ValidationResponse(
            valid=False,
            errors=[f"URL year ({year}) does not match rules fiscal_year ({rules.fiscal_year})"],
            warnings=[],
        )

    result = validate_rules(rules)
    return ValidationResponse(
        valid=result.valid,
        errors=result.errors,
        warnings=result.warnings,
    )


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload new fiscal rules",
    description="Upload and save fiscal rules for a year (overwrites existing)",
)
async def upload_rules(rules: FiscalRules) -> UploadResponse:
    """
    Upload fiscal rules for a year.

    Args:
        rules: The rules to save

    Returns:
        Upload result

    Raises:
        HTTPException: If rules are invalid
    """
    # Validate first
    result = validate_rules(rules)
    if not result.valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "INVALID_RULES",
                "message": "Rules validation failed",
                "errors": result.errors,
            },
        )

    # Save rules
    try:
        save_rules(rules)
        return UploadResponse(
            success=True,
            fiscal_year=rules.fiscal_year,
            message=f"Rules for {rules.fiscal_year} saved successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "SAVE_ERROR", "message": str(e)},
        )
