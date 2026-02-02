"""
Security Headers Middleware
===========================

Adds security headers to all HTTP responses to protect against
common web vulnerabilities.

Headers added:
- X-Content-Type-Options: Prevent MIME sniffing
- X-Frame-Options: Prevent clickjacking
- X-XSS-Protection: XSS filter (legacy browsers)
- Strict-Transport-Security: Enforce HTTPS
- Content-Security-Policy: Control resource loading
- Referrer-Policy: Control referrer information
- Permissions-Policy: Control browser features
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.

    Usage:
        from fastapi import FastAPI
        from src.app.middleware.security_headers import SecurityHeadersMiddleware

        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
    """

    def __init__(
        self,
        app: ASGIApp,
        # Content-Type Options
        content_type_options: str = "nosniff",
        # Frame Options
        frame_options: str = "DENY",
        # XSS Protection (for legacy browsers)
        xss_protection: str = "1; mode=block",
        # HSTS (set to None to disable)
        hsts_max_age: int | None = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,
        # CSP (set to None to disable)
        content_security_policy: str | None = "default-src 'self'",
        # Referrer Policy
        referrer_policy: str = "strict-origin-when-cross-origin",
        # Permissions Policy
        permissions_policy: str | None = "geolocation=(), microphone=(), camera=()",
        # Cache Control for sensitive endpoints
        cache_control: str | None = None,
    ):
        super().__init__(app)
        self.content_type_options = content_type_options
        self.frame_options = frame_options
        self.xss_protection = xss_protection
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        self.content_security_policy = content_security_policy
        self.referrer_policy = referrer_policy
        self.permissions_policy = permissions_policy
        self.cache_control = cache_control

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        if self.content_type_options:
            response.headers["X-Content-Type-Options"] = self.content_type_options

        # Prevent clickjacking
        if self.frame_options:
            response.headers["X-Frame-Options"] = self.frame_options

        # XSS protection for legacy browsers
        if self.xss_protection:
            response.headers["X-XSS-Protection"] = self.xss_protection

        # HTTP Strict Transport Security
        if self.hsts_max_age is not None:
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value

        # Content Security Policy
        if self.content_security_policy:
            response.headers["Content-Security-Policy"] = self.content_security_policy

        # Referrer Policy
        if self.referrer_policy:
            response.headers["Referrer-Policy"] = self.referrer_policy

        # Permissions Policy (formerly Feature-Policy)
        if self.permissions_policy:
            response.headers["Permissions-Policy"] = self.permissions_policy

        # Cache Control
        if self.cache_control:
            response.headers["Cache-Control"] = self.cache_control

        return response


class StrictSecurityHeadersMiddleware(SecurityHeadersMiddleware):
    """
    Pre-configured middleware with strict security settings.

    Suitable for applications handling sensitive data.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(
            app,
            content_type_options="nosniff",
            frame_options="DENY",
            xss_protection="1; mode=block",
            hsts_max_age=31536000,
            hsts_include_subdomains=True,
            hsts_preload=True,
            content_security_policy="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'",
            referrer_policy="no-referrer",
            permissions_policy="accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()",
            cache_control="no-store, no-cache, must-revalidate, private",
        )


class APISecurityHeadersMiddleware(SecurityHeadersMiddleware):
    """
    Pre-configured middleware for API-only applications.

    Less restrictive CSP since APIs don't serve HTML.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(
            app,
            content_type_options="nosniff",
            frame_options="DENY",
            xss_protection="0",  # Not needed for APIs
            hsts_max_age=31536000,
            hsts_include_subdomains=True,
            hsts_preload=False,
            content_security_policy=None,  # Not applicable for JSON APIs
            referrer_policy="no-referrer",
            permissions_policy=None,  # Not applicable for APIs
            cache_control="no-store",
        )
