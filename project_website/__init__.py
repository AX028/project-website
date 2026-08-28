"""Application factory for the Project Simulation portfolio."""

from __future__ import annotations

import os
from typing import Any

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .extensions import csrf, limiter
from .github import GitHubProjectClient
from .routes import site


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "development-only-change-me"),
        MAX_CONTENT_LENGTH=16 * 1024,
        WTF_CSRF_TIME_LIMIT=3600,
        RATELIMIT_STORAGE_URI="memory://",
        CACHE_TTL_SECONDS=int(os.getenv("CACHE_TTL_SECONDS", "600")),
        GITHUB_TOKEN=os.getenv("GITHUB_TOKEN"),
        CONTACT_RECIPIENT=os.getenv("CONTACT_RECIPIENT"),
        CONTACT_SENDER=os.getenv("CONTACT_SENDER"),
        SMTP_HOST=os.getenv("SMTP_HOST"),
        SMTP_PORT=int(os.getenv("SMTP_PORT", "587")),
        SMTP_USERNAME=os.getenv("SMTP_USERNAME"),
        SMTP_PASSWORD=os.getenv("SMTP_PASSWORD"),
        SMTP_USE_TLS=os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"},
    )
    if test_config:
        app.config.update(test_config)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)  # type: ignore[method-assign]
    csrf.init_app(app)
    limiter.init_app(app)
    app.extensions["github_projects"] = GitHubProjectClient(
        token=app.config["GITHUB_TOKEN"], ttl_seconds=app.config["CACHE_TTL_SECONDS"]
    )
    app.register_blueprint(site)

    @app.after_request
    def security_headers(response: Any) -> Any:
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()"
        )
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; "
            "connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'self'",
        )
        if not app.debug and not app.testing:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        return response

    return app
