"""API authentication via Bearer token in the Authorization header."""

import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import Environment, get_settings

_bearer_scheme = HTTPBearer(auto_error=False)


async def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    """Require `Authorization: Bearer <token>` on protected routes."""
    settings = get_settings()

    if not settings.API_TOKEN:
        if settings.environment is Environment.DEVELOPMENT:
            return ""
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_TOKEN is not configured on the server",
        )

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Use: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Constant-time comparison to avoid leaking the token through timing.
    if not secrets.compare_digest(credentials.credentials, settings.API_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials
