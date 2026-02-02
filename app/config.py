"""Application configuration."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Mortgage Monthly Costs Calculator"
    app_version: str = "1.0.0"
    debug: bool = False

    # Rules directory (relative to app root)
    rules_dir: Path = Path(__file__).parent / "rules"

    # Default fiscal year
    default_fiscal_year: int = 2026

    class Config:
        env_prefix = "MORTGAGE_"
        env_file = ".env"


settings = Settings()
