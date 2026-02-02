"""Fiscal rules validation."""

from decimal import Decimal

from app.api.schemas.rules import FiscalRules


class RulesValidationResult:
    """Result of rules validation."""

    def __init__(self) -> None:
        self.valid = True
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def add_error(self, message: str) -> None:
        """Add an error."""
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning."""
        self.warnings.append(message)


def validate_rules(rules: FiscalRules) -> RulesValidationResult:
    """
    Validate fiscal rules for consistency and sanity.

    Args:
        rules: The rules to validate

    Returns:
        RulesValidationResult with errors and warnings
    """
    result = RulesValidationResult()

    # Validate tax brackets
    _validate_tax_brackets(rules, result)

    # Validate EWF table
    _validate_ewf_table(rules, result)

    # Validate max deduction rate
    _validate_max_deduction_rate(rules, result)

    # Validate Hillen
    _validate_hillen(rules, result)

    return result


def _validate_tax_brackets(rules: FiscalRules, result: RulesValidationResult) -> None:
    """Validate tax brackets are properly structured."""
    brackets = rules.tax_brackets_box1

    if not brackets:
        result.add_error("tax_brackets_box1 is empty")
        return

    # Check brackets are ascending
    sorted_brackets = sorted(brackets, key=lambda b: b.lower)

    for i, bracket in enumerate(sorted_brackets):
        # Check rate is valid
        if bracket.rate < 0 or bracket.rate > 1:
            result.add_error(
                f"Tax bracket {i}: rate {bracket.rate} should be between 0 and 1"
            )

        # Check continuity
        if i > 0:
            prev = sorted_brackets[i - 1]
            if prev.upper is not None and prev.upper != bracket.lower:
                result.add_warning(
                    f"Gap in tax brackets between {prev.upper} and {bracket.lower}"
                )

    # Check last bracket is unlimited
    last = sorted_brackets[-1]
    if last.upper is not None:
        result.add_warning("Last tax bracket should have unlimited upper bound")


def _validate_ewf_table(rules: FiscalRules, result: RulesValidationResult) -> None:
    """Validate EWF table is properly structured."""
    table = rules.ewf_table

    if not table:
        result.add_error("ewf_table is empty")
        return

    # Check bands don't overlap
    sorted_bands = sorted(table, key=lambda b: b.lower)

    for i, band in enumerate(sorted_bands):
        # Check percentages are valid
        if band.percentage is not None:
            if band.percentage < 0 or band.percentage > 1:
                result.add_error(
                    f"EWF band {i}: percentage {band.percentage} should be between 0 and 1"
                )

        if band.excess_percentage is not None:
            if band.excess_percentage < 0 or band.excess_percentage > 1:
                result.add_error(
                    f"EWF band {i}: excess_percentage should be between 0 and 1"
                )

        # Check for overlap
        if i > 0:
            prev = sorted_bands[i - 1]
            if prev.upper is not None and prev.upper >= band.lower:
                if prev.upper > band.lower:
                    result.add_error(
                        f"EWF bands overlap: {prev.lower}-{prev.upper} and {band.lower}-{band.upper}"
                    )

    # Check there's a band starting at 0
    if sorted_bands[0].lower > 0:
        result.add_error("EWF table should have a band starting at 0")


def _validate_max_deduction_rate(
    rules: FiscalRules, result: RulesValidationResult
) -> None:
    """Validate maximum deduction rate."""
    rate = rules.max_mortgage_interest_deduction_rate

    if rate < 0 or rate > 1:
        result.add_error(
            f"max_mortgage_interest_deduction_rate {rate} should be between 0 and 1"
        )

    # Check it's not higher than highest tax bracket
    max_bracket_rate = max(b.rate for b in rules.tax_brackets_box1)
    if rate > max_bracket_rate:
        result.add_warning(
            f"max_mortgage_interest_deduction_rate ({rate}) is higher than "
            f"highest tax bracket rate ({max_bracket_rate})"
        )


def _validate_hillen(rules: FiscalRules, result: RulesValidationResult) -> None:
    """Validate Hillen configuration."""
    hillen = rules.hillen

    if hillen.reduction_percentage < 0 or hillen.reduction_percentage > 1:
        result.add_error(
            f"Hillen reduction_percentage {hillen.reduction_percentage} "
            "should be between 0 and 1"
        )
