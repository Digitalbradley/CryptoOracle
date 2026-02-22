"""Authentication service — password hashing and JWT management."""

import logging
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(username: str) -> str:
    """Create a JWT access token with expiry."""
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours)
    payload = {
        "sub": username,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    """Decode a JWT token and return the username, or None if invalid/expired."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        username: str | None = payload.get("sub")
        return username
    except JWTError:
        return None


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """Validate credentials and return the User, or None."""
    user = db.execute(
        select(User).where(User.username == username.lower())
    ).scalar_one_or_none()

    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def ensure_admin_user(db: Session) -> None:
    """Create the admin user from env vars if no users exist.

    Called during application startup (lifespan).
    """
    existing = db.execute(select(User).limit(1)).scalar_one_or_none()
    if existing is not None:
        logger.info("Admin user already exists, skipping seed.")
        return

    if not settings.admin_password:
        logger.warning(
            "No ADMIN_PASSWORD set and no users in database. "
            "Set ADMIN_PASSWORD env var and restart to create admin user."
        )
        return

    user = User(
        username=settings.admin_username,
        hashed_password=hash_password(settings.admin_password),
    )
    db.add(user)
    db.commit()
    logger.info("Admin user '%s' created from env vars.", settings.admin_username)
