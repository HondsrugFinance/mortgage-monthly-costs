"""Wet Hillen calculation module."""

from decimal import ROUND_HALF_UP, Decimal

from app.api.schemas.rules import HillenConfig


def _round_currency(value: Decimal) -> Decimal:
    """Round to 2 decimal places using HALF_UP."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_hillen_deduction(
    ewf: Decimal,
    deductible_interest: Decimal,
    hillen_config: HillenConfig,
) -> Decimal:
    """
    Calculate the Hillen deduction (aftrek wegens geen of geringe eigenwoningschuld).

    The Hillen arrangement applies when the deductible mortgage interest is less
    than the eigenwoningforfait (EWF). In this case, part of the difference
    can be deducted to reduce the net EWF addition.

    Since 2019, the Hillen deduction is being phased out gradually.
    The reduction_percentage indicates what portion of the difference
    can still be deducted.

    Args:
        ewf: Annual eigenwoningforfait amount
        deductible_interest: Annual deductible mortgage interest (box 1)
        hillen_config: Hillen configuration for the fiscal year

    Returns:
        Annual Hillen deduction amount (to be subtracted from EWF)
    """
    if not hillen_config.enabled:
        return Decimal("0")

    # Hillen only applies when interest < EWF
    if deductible_interest >= ewf:
        return Decimal("0")

    # Calculate the difference
    difference = ewf - deductible_interest

    # Apply the reduction percentage (phased out over time)
    hillen_deduction = difference * hillen_config.reduction_percentage

    return _round_currency(hillen_deduction)


def calculate_net_ewf_addition(
    ewf: Decimal,
    deductible_interest: Decimal,
    hillen_config: HillenConfig,
) -> Decimal:
    """
    Calculate the net EWF addition after Hillen deduction.

    This is the amount that will be added to taxable income.

    Args:
        ewf: Annual eigenwoningforfait amount
        deductible_interest: Annual deductible mortgage interest (box 1)
        hillen_config: Hillen configuration for the fiscal year

    Returns:
        Net annual EWF addition to taxable income
    """
    hillen = calculate_hillen_deduction(ewf, deductible_interest, hillen_config)
    net_ewf = ewf - hillen
    return max(Decimal("0"), net_ewf)
