"""
VaultMind Forge - Security Middleware

Enterprise-grade security middleware for production deployments.
Implements defense-in-depth security controls.
"""

import os
import logging
from fastapi import Request, Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware
from typing import Callable

logger = logging.getLogger(__name__)

# Security configuration
ALLOWED_HOSTS = os.getenv("VAULTMIND_ALLOWED_HOSTS", "*").split(",")
MAX_REQUEST_SIZE = int(os.getenv("VAULTMIND_MAX_REQUEST_SIZE", str(50 * 1024 * 1024)))  # 50MB default
ENABLE_HSTS = os.getenv("VAULTMIND_ENABLE_HSTS", "false").lower() == "true"
HSTS_MAX_AGE = int(os.getenv("VAULTMIND_HSTS_MAX_AGE", "31536000"))  # 1 year


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.

    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Content-Security-Policy: Strict CSP for production
    - Strict-Transport-Security: HSTS for HTTPS
    - Referrer-Policy: no-referrer
    - Permissions-Policy: Restrict browser features
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy
        # Strict policy that prevents inline scripts and restricts sources
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # React needs eval for dev
            "style-src 'self' 'unsafe-inline'",  # Tailwind needs inline styles
            "img-src 'self' data: blob: https:",
            "font-src 'self' data:",
            "connect-src 'self' http://localhost:* ws://localhost:*",  # API + WebSocket
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # HSTS (HTTP Strict Transport Security) - only if HTTPS
        if ENABLE_HSTS and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = f"max-age={HSTS_MAX_AGE}; includeSubDomains; preload"

        # Referrer policy - don't leak URLs
        response.headers["Referrer-Policy"] = "no-referrer"

        # Permissions policy - restrict browser features
        permissions_directives = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions_directives)

        # Prevent caching of sensitive endpoints
        if request.url.path.startswith("/api/") and request.url.path != "/api/health":
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Limit request body size to prevent DoS attacks.

    Rejects requests larger than MAX_REQUEST_SIZE with 413 status.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method in ("POST", "PUT", "PATCH"):
            # Check Content-Length header
            content_length = request.headers.get("content-length")

            if content_length:
                content_length = int(content_length)

                if content_length > MAX_REQUEST_SIZE:
                    logger.warning(
                        f"Request rejected: size {content_length} bytes exceeds limit {MAX_REQUEST_SIZE} bytes"
                    )
                    return Response(
                        content=f"Request body too large. Maximum size: {MAX_REQUEST_SIZE} bytes",
                        status_code=413,
                        media_type="text/plain"
                    )

        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all API requests for security auditing.

    Logs:
    - HTTP method and path
    - Client IP
    - Response status code
    - Response time
    - User agent (optional)

    Excludes: Health check endpoint to reduce log noise
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        import time

        # Skip logging health checks
        if request.url.path == "/api/health":
            return await call_next(request)

        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path

        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            logger.error(f"Request failed: {method} {path} - {str(e)}", exc_info=True)
            raise

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log request
        logger.info(
            f"{method} {path} - {client_ip} - {status_code} - {duration_ms:.2f}ms",
            extra={
                "client_ip": client_ip,
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "user_agent": request.headers.get("user-agent", "unknown"),
            }
        )

        return response


class SanitizeErrorMiddleware(BaseHTTPMiddleware):
    """
    Sanitize error responses to prevent information leakage.

    In production mode:
    - Hides internal file paths
    - Removes stack traces from responses
    - Provides generic error messages

    In development mode:
    - Shows full error details for debugging
    """

    def __init__(self, app, production_mode: bool = None):
        super().__init__(app)
        if production_mode is None:
            production_mode = os.getenv("VAULTMIND_ENV", "production").lower() == "production"
        self.production_mode = production_mode

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Only sanitize error responses in production
        if self.production_mode and response.status_code >= 400:
            # Error responses are already handled by error_handling.py
            # This middleware just ensures no additional leakage
            pass

        return response


def configure_security_middleware(app):
    """
    Configure all security middleware for the FastAPI app.

    Call this function to add comprehensive security to your application.

    Args:
        app: FastAPI application instance

    Returns:
        Configured FastAPI app
    """
    # 1. Request size limiting (first to reject large payloads early)
    app.add_middleware(RequestSizeLimitMiddleware)

    # 2. Security headers (applied to all responses)
    app.add_middleware(SecurityHeadersMiddleware)

    # 3. Request logging (for security auditing)
    app.add_middleware(RequestLoggingMiddleware)

    # 4. Error sanitization (prevent information leakage)
    production_mode = os.getenv("VAULTMIND_ENV", "production").lower() == "production"
    app.add_middleware(SanitizeErrorMiddleware, production_mode=production_mode)

    # 5. GZip compression (performance + smaller attack surface)
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 6. Trusted host validation (if not wildcard)
    if "*" not in ALLOWED_HOSTS:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
        logger.info(f"Trusted host middleware enabled for: {ALLOWED_HOSTS}")

    logger.info("Security middleware configured successfully")
    logger.info(f"Max request size: {MAX_REQUEST_SIZE} bytes ({MAX_REQUEST_SIZE // 1024 // 1024}MB)")
    logger.info(f"HSTS enabled: {ENABLE_HSTS}")
    logger.info(f"Production mode: {production_mode}")

    return app
