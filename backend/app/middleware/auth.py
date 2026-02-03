"""
Nekazari Odoo ERP Module - JWT Authentication Middleware

Validates JWT tokens from Keycloak.

Author: Kate Benetis <kate@robotika.cloud>
Company: Robotika
License: AGPL-3.0
"""

import logging
from typing import Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import jwt
from jwt import PyJWKClient
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Cache for JWKS client
_jwks_client: Optional[PyJWKClient] = None


def get_jwks_client() -> PyJWKClient:
    """Get or create JWKS client for token validation."""
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(settings.jwks_url)
    return _jwks_client


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to validate JWT tokens from Keycloak."""

    # Paths that don't require authentication
    EXEMPT_PATHS = {
        "/",
        "/api/odoo/health",
        "/api/odoo/webhook/ngsi",  # NGSI-LD subscriptions (validated differently)
        "/api/odoo/webhook/n8n",   # N8N webhooks (validated by secret)
        "/docs",
        "/redoc",
        "/openapi.json"
    }

    async def dispatch(self, request: Request, call_next):
        """Process the request and validate JWT if needed."""

        # Skip auth for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Skip auth for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Get Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing Authorization header"}
            )

        # Extract token
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid auth scheme")
        except ValueError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid Authorization header format"}
            )

        # Validate token
        try:
            payload = await self.validate_token(token)
            request.state.user = payload
            request.state.tenant_id = self.extract_tenant_id(request, payload)
        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token has expired"}
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token"}
            )
        except Exception as e:
            logger.error(f"Auth error: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Authentication error"}
            )

        return await call_next(request)

    async def validate_token(self, token: str) -> dict:
        """Validate JWT token and return payload."""
        try:
            jwks_client = get_jwks_client()
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            
            expected_issuer = f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}"

            # Keycloak tokens may not include 'aud' claim depending on configuration
            # Validate signature and issuer, skip audience validation
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=expected_issuer,
                options={"verify_aud": False}
            )
            
            logger.debug(f"Token validated for user: {payload.get('preferred_username', 'unknown')}")
            return payload

        except jwt.PyJWKClientError as e:
            logger.error(f"JWKS client error: {e}")
            raise jwt.InvalidTokenError("Could not validate token")

    def extract_tenant_id(self, request: Request, payload: dict) -> Optional[str]:
        """Extract tenant ID from request or token."""
        # First try X-Tenant-ID header
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            return tenant_id

        # Try to get from token claims
        # Keycloak can include tenant in resource_access or custom claims
        resource_access = payload.get("resource_access", {})
        nekazari_access = resource_access.get("nekazari-api", {})
        tenant_id = nekazari_access.get("tenant_id")

        if tenant_id:
            return tenant_id

        # Try custom claim
        return payload.get("tenant_id")


def get_current_user(request: Request) -> dict:
    """Dependency to get current user from request state."""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def get_current_tenant(request: Request) -> str:
    """Dependency to get current tenant ID from request state."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant ID not found")
    return tenant_id
