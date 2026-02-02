"""FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, Query

from app.api.schemas.rules import FiscalRules
from app.config import settings
from app.domain.calculator import MortgageCalculator
from app.rules.loader import load_rules


def get_fiscal_rules(
    fiscal_year: Annotated[
        int,
        Query(description="Fiscal year for rules", ge=2020, le=2050),
    ] = None,
) -> FiscalRules:
    """
    Dependency to get fiscal rules for a year.

    Args:
        fiscal_year: The fiscal year (defaults to configured default)

    Returns:
        FiscalRules for the requested year
    """
    year = fiscal_year or settings.default_fiscal_year
    return load_rules(year)


def get_calculator(
    fiscal_year: Annotated[
        int,
        Query(description="Fiscal year for calculation", ge=2020, le=2050),
    ] = None,
) -> MortgageCalculator:
    """
    Dependency to get a calculator instance.

    Args:
        fiscal_year: The fiscal year (defaults to configured default)

    Returns:
        MortgageCalculator instance for the requested year
    """
    year = fiscal_year or settings.default_fiscal_year
    return MortgageCalculator(year)
