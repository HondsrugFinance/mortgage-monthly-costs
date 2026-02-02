"""Pydantic schemas for API request/response validation."""

from app.api.schemas.input import (
    LoanPart,
    LoanType,
    MonthlyCostsRequest,
    Partner,
    PartnerDistribution,
    PartnerDistributionMethod,
)
from app.api.schemas.output import (
    LoanPartResult,
    MonthlyCostsResponse,
    PartnerResult,
    TaxBreakdown,
)
from app.api.schemas.rules import (
    EWFBand,
    FiscalRules,
    HillenConfig,
    TaxBracket,
)

__all__ = [
    # Input
    "LoanPart",
    "LoanType",
    "MonthlyCostsRequest",
    "Partner",
    "PartnerDistribution",
    "PartnerDistributionMethod",
    # Output
    "LoanPartResult",
    "MonthlyCostsResponse",
    "PartnerResult",
    "TaxBreakdown",
    # Rules
    "EWFBand",
    "FiscalRules",
    "HillenConfig",
    "TaxBracket",
]
