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
        "/api/odoo/internal/lifecycle",  # Module lifecycle (validated by HMAC)
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

        # Extract token from Authorization header or httpOnly cookie fallback
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header:
            try:
                scheme, token = auth_header.split()
                if scheme.lower() != "bearer":
                    token = None
            except ValueError:
                token = None

        if not token:
            token = request.cookies.get("nkz_token")

        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authentication (Bearer token or session cookie)"}
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

            # Build issuer whitelist (internal + public, with/without /auth)
            allowed_issuers = set()
            realm_suffix = f"/realms/{settings.KEYCLOAK_REALM}"

            for base_url in [settings.KEYCLOAK_URL, settings.KEYCLOAK_PUBLIC_URL]:
                if not base_url:
                    continue
                clean = base_url.rstrip("/")
                if "/auth" not in clean and not clean.endswith("/realms"):
                    clean = f"{clean}/auth"
                allowed_issuers.add(f"{clean}{realm_suffix}")
                # Also add without /auth variant (modern Keycloak)
                allowed_issuers.add(f"{clean.replace('/auth', '')}{realm_suffix}")

            # Keycloak tokens may not include 'aud' claim depending on configuration
            # Validate signature, skip audience and issuer validation (manual check below)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_aud": False, "verify_iss": False},
            )

            # Manual issuer validation with /auth flexibility
            token_iss = payload.get("iss", "")
            is_valid = token_iss in allowed_issuers
            if not is_valid and token_iss:
                clean_iss = token_iss.replace("/auth/realms/", "/realms/")
                for base in list(allowed_issuers):
                    clean_base = base.replace("/auth/realms/", "/realms/")
                    if clean_base == clean_iss:
                        is_valid = True
                        break

            if not is_valid:
                logger.warning(
                    "Token issuer %s not in allowed issuers %s",
                    token_iss, allowed_issuers,
                )
                raise jwt.InvalidTokenError("Invalid token issuer")

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
