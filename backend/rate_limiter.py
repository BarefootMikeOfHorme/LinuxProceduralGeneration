"""
Rate Limiting Middleware for VaultMind Forge API

Prevents DoS attacks and abuse by limiting request rates per client.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
import os

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute", "1000/hour"],  # Global limits
    storage_uri=os.getenv("RATE_LIMIT_STORAGE", "memory://"),  # Can use Redis in production
    headers_enabled=True,  # Add X-RateLimit-* headers to responses
)

# Rate limit configurations for different endpoint types
RATE_LIMITS = {
    # Expensive operations - very limited
    "execute_workflow": "5/minute",      # Workflow execution is resource-intensive
    "generate": "10/minute",             # AI generation is expensive

    # Moderate operations
    "save_workflow": "30/minute",        # Saving workflows
    "list_workflows": "60/minute",       # Listing operations

    # Light operations
    "health_check": "300/minute",        # Health checks can be frequent
    "auth_status": "60/minute",          # Auth checks

    # File operations
    "browse_filesystem": "120/minute",   # Directory browsing
    "get_thumbnail": "200/minute",       # Thumbnail generation
}

def get_rate_limit(endpoint_name: str) -> str:
    """Get rate limit for specific endpoint"""
    return RATE_LIMITS.get(endpoint_name, "100/minute")  # Default fallback


async def rate_limit_by_api_key(request: Request) -> str:
    """
    Custom key function that uses API key instead of IP address.
    This is better for APIs where multiple users may share an IP.
    """
    # Try to get API key from headers
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key}"

    # Fallback to IP address
    return f"ip:{get_remote_address(request)}"
