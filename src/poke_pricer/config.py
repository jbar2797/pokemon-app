from __future__ import annotations

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment/.env with prefix POKEPRICER_."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="POKEPRICER_",
        case_sensitive=False,
    )

    # Core
    debug: bool = False
    log_level: str = "INFO"
    data_dir: Path = Path("data")

    # API credentials (optional until wired)
    tcgplayer_public_key: SecretStr | None = None
    tcgplayer_private_key: SecretStr | None = None
    ebay_app_id: SecretStr | None = None
    psa_api_key: SecretStr | None = None
    cgc_api_key: SecretStr | None = None

    # Optional database DSN
    postgres_dsn: str | None = None

    def as_public_dict(self) -> dict[str, str]:
        """Return a sanitized dict for safe display/logging."""

        def mask(val: SecretStr | None) -> str:
            return "***" if val is not None else ""

        return {
            "debug": str(self.debug),
            "log_level": self.log_level,
            "data_dir": str(self.data_dir),
            "tcgplayer_public_key": mask(self.tcgplayer_public_key),
            "tcgplayer_private_key": mask(self.tcgplayer_private_key),
            "ebay_app_id": mask(self.ebay_app_id),
            "psa_api_key": mask(self.psa_api_key),
            "cgc_api_key": mask(self.cgc_api_key),
            "postgres_dsn": "***" if self.postgres_dsn else "",
        }


__all__ = ["Settings"]
