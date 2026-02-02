"""Exception handlers for FastAPI."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions import (
    CalculationError,
    FiscalRulesNotFoundError,
    MortgageCalculatorError,
    ValidationError,
)


async def mortgage_calculator_exception_handler(
    request: Request,
    exc: MortgageCalculatorError,
) -> JSONResponse:
    """Handle custom mortgage calculator exceptions."""
    status_code = status.HTTP_400_BAD_REQUEST

    if isinstance(exc, FiscalRulesNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, ValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, CalculationError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(
        status_code=status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    errors = []
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])
        errors.append({"field": field_path, "message": error["msg"]})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "validation_errors": errors,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(MortgageCalculatorError, mortgage_calculator_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
