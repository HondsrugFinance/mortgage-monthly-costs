"""Fiscal rules loader with caching."""

import json
from functools import lru_cache
from pathlib import Path

from app.api.schemas.rules import FiscalRules
from app.config import settings
from app.exceptions import FiscalRulesNotFoundError, InvalidFiscalRulesError


@lru_cache(maxsize=10)
def load_rules(fiscal_year: int) -> FiscalRules:
    """
    Load fiscal rules for a specific year.

    Rules are loaded from JSON files in the rules directory.
    Results are cached for performance.

    Args:
        fiscal_year: The year to load rules for

    Returns:
        FiscalRules object with all rules

    Raises:
        FiscalRulesNotFoundError: If no rules file exists for the year
        InvalidFiscalRulesError: If the rules file is invalid
    """
    rules_file = settings.rules_dir / f"{fiscal_year}.json"

    if not rules_file.exists():
        raise FiscalRulesNotFoundError(fiscal_year)

    try:
        with open(rules_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        rules = FiscalRules.model_validate(data)
        return rules

    except json.JSONDecodeError as e:
        raise InvalidFiscalRulesError(
            message=f"Invalid JSON in rules file: {e}",
            year=fiscal_year,
        )
    except Exception as e:
        raise InvalidFiscalRulesError(
            message=f"Error loading rules: {e}",
            year=fiscal_year,
        )


def get_available_years() -> list[int]:
    """
    Get list of years for which rules are available.

    Returns:
        List of fiscal years with available rules
    """
    rules_dir = settings.rules_dir
    if not rules_dir.exists():
        return []

    years = []
    for file in rules_dir.glob("*.json"):
        try:
            year = int(file.stem)
            years.append(year)
        except ValueError:
            continue

    return sorted(years)


def save_rules(rules: FiscalRules) -> Path:
    """
    Save fiscal rules to a JSON file.

    Args:
        rules: The rules to save

    Returns:
        Path to the saved file
    """
    rules_dir = settings.rules_dir
    rules_dir.mkdir(parents=True, exist_ok=True)

    rules_file = rules_dir / f"{rules.fiscal_year}.json"

    with open(rules_file, "w", encoding="utf-8") as f:
        json.dump(rules.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

    # Clear cache for this year
    load_rules.cache_clear()

    return rules_file


def clear_cache() -> None:
    """Clear the rules cache."""
    load_rules.cache_clear()
