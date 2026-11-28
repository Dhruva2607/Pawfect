"""
Adopter authentication helpers.

PawFect's adopter accounts remain demo-grade (no password verification), but
identity is still enforced: an adopter may only act on their own resources.
The token format `token_<user_id>` is validated here and never trusted from a
query parameter alone.
"""

from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from app.services.auth import decode_jwt_token

ADOPTER_TOKEN_PREFIX = "token_"


def user_id_from_token(token: str) -> Optional[str]:
    """Return the adopter user id encoded in a demo token, or None if not one."""
    if not token.startswith(ADOPTER_TOKEN_PREFIX):
        return None
    user_id = token[len(ADOPTER_TOKEN_PREFIX):].strip()
    return user_id or None


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header.",
        )
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'.",
        )
    return parts[1].strip()


def resolve_adopter_id(authorization: Optional[str]) -> Optional[str]:
    """
    Resolve the adopter id from an Authorization header, tolerating a shelter JWT
    (which identifies a non-adopter and therefore yields None).
    """
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    adopter_id = user_id_from_token(token)
    if adopter_id:
        return adopter_id
    if token.startswith(ADOPTER_TOKEN_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed adopter token.",
        )
    # Could be a shelter JWT; verify it so a garbage token does not silently pass.
    payload = decode_jwt_token(token)
    if payload.get("role") == "shelter":
        return None
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Adopter credentials required.",
    )


async def get_current_adopter(
    authorization: Optional[str] = Header(default=None),
) -> str:
    """FastAPI dependency returning the authenticated adopter's user id."""
    token = _extract_bearer_token(authorization)
    adopter_id = user_id_from_token(token)
    if adopter_id:
        return adopter_id
    payload = decode_jwt_token(token)
    if payload.get("role") == "shelter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Shelter credentials cannot be used for adopter endpoints.",
        )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Adopter credentials required.",
    )


def require_self(claimed_id: str, authenticated_id: str) -> None:
    """Raise 403 unless the authenticated adopter owns the claimed resource id."""
    if claimed_id != authenticated_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You may only access your own account.",
        )


CurrentAdopter = Depends(get_current_adopter)
