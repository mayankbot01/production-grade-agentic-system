import re
from datetime import UTC, datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from src.config.settings import settings
from src.data.schemas.auth import Token
from src.utils.sanitization import sanitize_string


# ==================================================
# JWT Authentication Utilities
# ==================================================
def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> Token:
    """
    Creates a new JWT access token.

    Args:
        subject: The unique identifier (User ID or Session ID)
        expires_delta: Optional custom expiration time
    """
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(days=settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(UTC),
        "jti": sanitize_string(f"{subject}-{datetime.now(UTC).timestamp()}"),
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return Token(access_token=encoded_jwt, expires_at=expire)


def verify_token(token: str) -> Optional[str]:
    """
    Decodes and verifies a JWT token. Returns the subject (User ID) if valid.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        subject: str = payload.get("sub")
        if subject is None:
            return None
        return subject
    except JWTError:
        return None
