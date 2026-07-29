"""API authentication via Bearer token in the Authorization header."""

import hashlib
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import Environment, get_settings

_bearer_scheme = HTTPBearer(auto_error=False)

# Length of the hex digest kept as an identity. 16 hex chars (64 bits) is far
# beyond collision range for the number of tokens this service will ever see,
# while staying short enough to read in a log line.
_USER_ID_DIGEST_CHARS = 16


def get_user_id(token: str | None) -> str:
    """Return a stable, non-reversible identifier derived from a bearer token.

    The raw token is a live credential: it must never be logged, nor retained
    as a dict key (rate-limit buckets outlive the request). Hashing here — at
    the single boundary every caller goes through — means no downstream code
    can leak it by accident.
    """
    if not token:
        return "anonymous"
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:_USER_ID_DIGEST_CHARS]


async def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    """Require `Authorization: Bearer <token>` on protected routes."""
    settings = get_settings()

    if not settings.API_TOKEN:
        if settings.ALLOW_UNAUTHENTICATED and settings.environment is Environment.DEVELOPMENT:
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
