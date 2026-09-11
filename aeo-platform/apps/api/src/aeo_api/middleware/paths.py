"""Shared path classification for API middleware."""

PUBLIC_PATHS: frozenset[str] = frozenset(
    {
        "/",
        "/health",
        "/ready",
        "/metrics",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/docs/oauth2-redirect",
        "/api/v1/auth/login",
        "/api/v1/auth/signup",
        "/api/v1/auth/refresh",
    }
)


def is_public_path(path: str) -> bool:
    return path in PUBLIC_PATHS
