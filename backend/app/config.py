"""
Nekazari Odoo ERP Module - Configuration

Environment-based configuration using Pydantic Settings.

Author: Kate Benetis <kate@robotika.cloud>
Company: Robotika
License: AGPL-3.0
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Settings
    API_TITLE: str = "Nekazari Odoo ERP Module API"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Odoo Connection
    ODOO_HOST: str = "odoo-service"
    ODOO_PORT: int = 8069
    ODOO_MASTER_PASSWORD: str = "admin"  # For database management
    ODOO_TEMPLATE_DB: str = "nkz_odoo_template"

    # PostgreSQL for Odoo
    ODOO_DB_HOST: str = "postgres-odoo-service"
    ODOO_DB_PORT: int = 5432
    ODOO_DB_USER: str = "odoo"
    ODOO_DB_PASSWORD: str = ""

    # Nekazari Platform Database (for sync mappings)
    DATABASE_URL: str = "postgresql://postgres:postgres@postgresql-service:5432/nekazari"

    # Redis for job queue
    REDIS_URL: str = "redis://redis-service:6379/0"

    # Keycloak
    KEYCLOAK_URL: str = "https://auth.artotxiki.com/auth"
    KEYCLOAK_REALM: str = "nekazari"
    KEYCLOAK_CLIENT_ID: str = "nekazari-api"
    JWKS_URL: str = ""

    # NGSI-LD Context Broker
    ORION_URL: str = "http://orion-ld-service:1026"

    # N8N Integration
    N8N_URL: str = "http://n8n-service:5678"
    N8N_WEBHOOK_SECRET: str = ""

    # Intelligence Module
    INTELLIGENCE_API_URL: str = "http://intelligence-api-service:8000"

    # Allowed Origins for CORS
    ALLOWED_ORIGINS: list[str] = [
        "https://nekazari.artotxiki.com",
        "http://localhost:5010",
        "http://localhost:5173"
    ]

    @property
    def odoo_url(self) -> str:
        """Get full Odoo URL."""
        return f"http://{self.ODOO_HOST}:{self.ODOO_PORT}"

    @property
    def jwks_url(self) -> str:
        """Get JWKS URL for token validation."""
        if self.JWKS_URL:
            return self.JWKS_URL
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}/protocol/openid-connect/certs"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
