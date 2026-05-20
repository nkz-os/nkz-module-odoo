"""
Tests for JWT token validation in JWTAuthMiddleware.

Covers the issuer whitelist fix: both internal (KEYCLOAK_URL) and
public (KEYCLOAK_PUBLIC_URL) issuers must be accepted.
"""

import time
import pytest
from unittest.mock import patch
import jwt as pyjwt

from app.middleware.auth import JWTAuthMiddleware
from app.config import settings


INTERNAL_ISSUER = "http://keycloak:8080/auth/realms/nekazari"
PUBLIC_ISSUER = "https://auth.robotika.cloud/auth/realms/nekazari"
UNKNOWN_ISSUER = "https://evil.example.com/auth/realms/nekazari"

HEADER = {"kid": "test-key-1", "alg": "RS256"}


def _make_token(issuer: str, private_key_pem: bytes) -> str:
    """Create a signed JWT with the given issuer."""
    now = int(time.time())
    return pyjwt.encode(
        {
            "iss": issuer,
            "sub": "user-1",
            "aud": "account",
            "azp": "nekazari-frontend",
            "iat": now,
            "exp": now + 300,
            "preferred_username": "testuser",
            "email": "test@example.com",
            "tenant_id": "tenant-1",
        },
        private_key_pem,
        algorithm="RS256",
        headers=HEADER,
    )


@pytest.fixture(autouse=True)
def _patch_settings(monkeypatch):
    """Ensure KEYCLOAK_PUBLIC_URL is set for tests."""
    monkeypatch.setattr(settings, "KEYCLOAK_PUBLIC_URL", "https://auth.robotika.cloud/auth")


class TestValidateToken:
    @pytest.mark.asyncio
    async def test_accepts_internal_issuer(self, mock_jwks_client, rsa_keys):
        """Token with internal Keycloak issuer (KEYCLOAK_URL) is accepted."""
        private_pem, _ = rsa_keys
        token = _make_token(INTERNAL_ISSUER, private_pem)
        middleware = JWTAuthMiddleware(app=None)

        with patch("app.middleware.auth.get_jwks_client", return_value=mock_jwks_client):
            payload = await middleware.validate_token(token)

        assert payload["sub"] == "user-1"
        assert payload["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_accepts_public_issuer(self, mock_jwks_client, rsa_keys):
        """Token with public Keycloak issuer (KEYCLOAK_PUBLIC_URL) is accepted."""
        private_pem, _ = rsa_keys
        token = _make_token(PUBLIC_ISSUER, private_pem)
        middleware = JWTAuthMiddleware(app=None)

        with patch("app.middleware.auth.get_jwks_client", return_value=mock_jwks_client):
            payload = await middleware.validate_token(token)

        assert payload["iss"] == PUBLIC_ISSUER
        assert payload["preferred_username"] == "testuser"

    @pytest.mark.asyncio
    async def test_accepts_internal_issuer_without_auth_suffix(self, rsa_keys, mock_jwks_client):
        """Token with internal issuer without /auth path (modern Keycloak) is accepted."""
        private_pem, _ = rsa_keys
        token = _make_token("http://keycloak:8080/realms/nekazari", private_pem)
        middleware = JWTAuthMiddleware(app=None)

        with patch("app.middleware.auth.get_jwks_client", return_value=mock_jwks_client):
            payload = await middleware.validate_token(token)

        assert payload["sub"] == "user-1"

    @pytest.mark.asyncio
    async def test_accepts_public_issuer_without_auth_suffix(self, rsa_keys, mock_jwks_client):
        """Token with public issuer without /auth path (modern Keycloak) is accepted."""
        private_pem, _ = rsa_keys
        token = _make_token("https://auth.robotika.cloud/realms/nekazari", private_pem)
        middleware = JWTAuthMiddleware(app=None)

        with patch("app.middleware.auth.get_jwks_client", return_value=mock_jwks_client):
            payload = await middleware.validate_token(token)

        assert payload["iss"] == "https://auth.robotika.cloud/realms/nekazari"

    @pytest.mark.asyncio
    async def test_rejects_unknown_issuer(self, mock_jwks_client, rsa_keys):
        """Token from an unknown issuer is rejected."""
        private_pem, _ = rsa_keys
        token = _make_token(UNKNOWN_ISSUER, private_pem)
        middleware = JWTAuthMiddleware(app=None)

        with patch("app.middleware.auth.get_jwks_client", return_value=mock_jwks_client):
            with pytest.raises(pyjwt.InvalidTokenError, match="Invalid token issuer"):
                await middleware.validate_token(token)

    @pytest.mark.asyncio
    async def test_rejects_expired_token(self, mock_jwks_client, rsa_keys):
        """Expired tokens are still rejected by PyJWT."""
        private_pem, _ = rsa_keys
        now = int(time.time())
        token = pyjwt.encode(
            {
                "iss": INTERNAL_ISSUER,
                "sub": "user-1",
                "iat": now - 600,
                "exp": now - 300,
            },
            private_pem,
            algorithm="RS256",
            headers=HEADER,
        )
        middleware = JWTAuthMiddleware(app=None)

        with patch("app.middleware.auth.get_jwks_client", return_value=mock_jwks_client):
            with pytest.raises(pyjwt.InvalidTokenError):
                await middleware.validate_token(token)
