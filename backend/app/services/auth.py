"""
Authentication & authorization helpers for PawFect shelters.
Uses bcrypt for password hashing and PyJWT for signed shelter tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt
from fastapi import Depends, Header, HTTPException, status

from app.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET
from app.database.connection import get_async_db


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    if not password or not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_shelter_token(
    shelter_id: str,
    email: str,
    expires_minutes: int = JWT_EXPIRE_MINUTES,
) -> str:
    """Issue a signed JWT with role='shelter' and shelter_id."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": shelter_id,
        "shelter_id": shelter_id,
        "email": email,
        "role": "shelter",
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """Decode and verify a signed JWT."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )


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


async def get_current_shelter(
    authorization: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    """
    FastAPI dependency enforcing shelter authentication and ownership.
    Verifies the signed JWT, checks role == 'shelter', and loads the shelter document.
    """
    token = _extract_bearer_token(authorization)
    payload = decode_jwt_token(token)

    if payload.get("role") != "shelter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Shelter role required.",
        )

    shelter_id = payload.get("shelter_id") or payload.get("sub")
    if not shelter_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing shelter_id claim.",
        )

    db = get_async_db()
    shelter_doc = await db["shelters"].find_one({"_id": shelter_id})
    if not shelter_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Shelter account not found.",
        )

    return shelter_doc
