"""
VaultMind Forge - API Authentication
Simple API key authentication with optional bypass for local development
"""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from typing import Optional
import os
import secrets

# API Key configuration
API_KEY_HEADER = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)

# Get API key from environment or generate a dev key
API_KEY = os.getenv("VAULTMIND_API_KEY")
AUTH_ENABLED = os.getenv("VAULTMIND_AUTH_ENABLED", "false").lower() == "true"

# Generate a random API key if auth is enabled but no key is set
if AUTH_ENABLED and not API_KEY:
    API_KEY = secrets.token_urlsafe(32)
    print(f"[AUTH] Generated API key: {API_KEY}")
    print(f"[AUTH] Set VAULTMIND_API_KEY environment variable to persist this key")

# Log auth status
if AUTH_ENABLED:
    print(f"[AUTH] Authentication ENABLED - API key required")
else:
    print(f"[AUTH] Authentication DISABLED - open access (development mode)")
    print(f"[AUTH] Set VAULTMIND_AUTH_ENABLED=true to enable authentication")


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Verify API key for protected endpoints

    Args:
        api_key: API key from request header

    Returns:
        The valid API key

    Raises:
        HTTPException: If authentication fails
    """
    # Skip auth if disabled (local development)
    if not AUTH_ENABLED:
        return "dev-mode"

    # Check if API key is provided
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Verify API key
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    return api_key


def get_auth_status() -> dict:
    """Get authentication status info"""
    return {
        "enabled": AUTH_ENABLED,
        "has_key": API_KEY is not None,
        "key_length": len(API_KEY) if API_KEY else 0,
    }
