"""Application configuration settings."""

from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    app_name: str = "ValueRail"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database settings
    database_url: str = "sqlite:///./valuerail.db"
    
    # For PostgreSQL, use:
    # database_url: str = "postgresql://user:password@localhost:5432/valuerail"
    
    # CORS settings
    # Comma-separated list of allowed origins, or "*" for all
    # Example: CORS_ORIGINS=http://localhost:3000,https://example.com
    cors_origins: str = "*"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }
    
    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, v):
        """Parse debug setting, handling non-boolean values gracefully."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            v_upper = v.upper()
            # Only accept valid boolean strings, otherwise use default (False)
            if v_upper in ("TRUE", "1", "YES", "ON"):
                return True
            elif v_upper in ("FALSE", "0", "NO", "OFF", ""):
                return False
            # If it's something else (like "WARN"), ignore it and use default
            return False
        return bool(v) if v is not None else False
    
    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from environment variable."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
