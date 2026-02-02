"""Tax calculation module - marginal rates and brackets."""

from decimal import Decimal

from app.api.schemas.rules import TaxBracket


def calculate_marginal_rate(
    taxable_income: Decimal,
    brackets: list[TaxBracket],
    is_aow: bool = False,
) -> Decimal:
    """
    Determine the marginal tax rate based on taxable income.

    The marginal rate is the rate that applies to the last euro of income,
    which is used for calculating the benefit of deductions.

    Args:
        taxable_income: Annual taxable income in box 1
        brackets: List of tax brackets (sorted by lower bound)
        is_aow: Whether the person has reached AOW age (lower first bracket rate)

    Returns:
        The marginal tax rate as a decimal (e.g., 0.3756 for 37.56%)
    """
    if not brackets:
        return Decimal("0")

    # Sort brackets by lower bound (descending) to find the right bracket
    sorted_brackets = sorted(brackets, key=lambda b: b.lower, reverse=True)

    for bracket in sorted_brackets:
        if taxable_income > bracket.lower:
            return bracket.rate

    # If income is 0 or below first bracket, use lowest bracket rate
    return sorted_brackets[-1].rate


def calculate_effective_deduction_rate(
    marginal_rate: Decimal,
    max_deduction_rate: Decimal,
) -> Decimal:
    """
    Determine the effective deduction rate for mortgage interest.

    Since 2014, the maximum deduction rate for mortgage interest has been
    gradually reduced. This function applies that limitation.

    Args:
        marginal_rate: The taxpayer's marginal tax rate
        max_deduction_rate: The maximum allowed deduction rate for the fiscal year

    Returns:
        The effective deduction rate (minimum of marginal and max allowed)
    """
    return min(marginal_rate, max_deduction_rate)


def calculate_tax_on_income(
    taxable_income: Decimal,
    brackets: list[TaxBracket],
) -> Decimal:
    """
    Calculate total income tax based on brackets.

    This is useful for understanding the overall tax position,
    though not directly used for monthly cost calculation.

    Args:
        taxable_income: Annual taxable income
        brackets: List of tax brackets

    Returns:
        Total annual income tax
    """
    if taxable_income <= 0:
        return Decimal("0")

    total_tax = Decimal("0")
    remaining_income = taxable_income

    # Sort brackets by lower bound (ascending)
    sorted_brackets = sorted(brackets, key=lambda b: b.lower)

    for bracket in sorted_brackets:
        if remaining_income <= 0:
            break

        # Calculate taxable amount in this bracket
        bracket_lower = bracket.lower
        bracket_upper = bracket.upper if bracket.upper is not None else Decimal("Infinity")

        if taxable_income <= bracket_lower:
            continue

        taxable_in_bracket = min(remaining_income, bracket_upper - bracket_lower)
        if bracket_lower < taxable_income:
            taxable_in_bracket = min(
                taxable_income - bracket_lower,
                bracket_upper - bracket_lower if bracket_upper != Decimal("Infinity") else remaining_income,
            )

        tax_in_bracket = taxable_in_bracket * bracket.rate
        total_tax += tax_in_bracket
        remaining_income -= taxable_in_bracket

    return total_tax
