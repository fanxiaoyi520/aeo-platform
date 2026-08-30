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
    }
)


def is_public_path(path: str) -> bool:
    return path in PUBLIC_PATHS
