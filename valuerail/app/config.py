"""Application configuration settings."""

from typing import List
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
        "env_file_encoding": "utf-8"
    }
    
    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from environment variable."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
