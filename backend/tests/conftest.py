"""
Test fixtures for Odoo ERP module.
"""

import pytest
from unittest.mock import MagicMock, patch
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

# Generate a deterministic RSA key pair for tests (only once per session)
_private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend(),
)

_public_key = _private_key.public_key()

# PEM-encoded keys
PRIVATE_KEY_PEM = _private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

PUBLIC_KEY_PEM = _public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)

# Minimal JWK representation for PyJWT
JWK_KEY = {
    "kty": "RSA",
    "kid": "test-key-1",
    "n": "test",  # PyJWT's get_signing_key_from_jwt uses the JWK dict directly
    "e": "AQAB",
}


@pytest.fixture
def rsa_keys():
    """Return (private_pem, public_pem) RSA keys for test token generation."""
    return PRIVATE_KEY_PEM, PUBLIC_KEY_PEM


@pytest.fixture
def mock_jwks_client():
    """Return a mock PyJWKClient that returns a real signing key."""
    # Build a real PyJWK signing key from the JWK data
    import jwt
    from jwt import PyJWK

    jwk_dict = jwt.algorithms.RSAAlgorithm.to_jwk(_public_key, as_dict=True)
    # inject a kid so get_signing_key_from_jwt can match
    jwk_dict["kid"] = "test-key-1"

    signing_key = PyJWK(jwk_dict, algorithm="RS256")

    mock = MagicMock()
    mock.get_signing_key_from_jwt.return_value = signing_key
    return mock
