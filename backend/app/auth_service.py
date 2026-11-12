"""Password hashing and opaque server-side session management."""

from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import User, UserSession


_password_hasher = PasswordHash.recommended()
DEFAULT_SESSION_LIFETIME = timedelta(hours=12)
MAX_SESSION_LIFETIME = timedelta(days=7)


def _utc_now():
    return datetime.now(timezone.utc)


def _normalise_utc(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def hash_password(password: str) -> str:
    if not isinstance(password, str) or len(password) < 12:
        raise ValueError("Password must contain at least 12 characters.")
    if len(password) > 1024:
        raise ValueError("Password is too long.")
    return _password_hasher.hash(password)


def verify_password(password: str, encoded_hash: str | None) -> bool:
    if not isinstance(password, str) or len(password) > 1024:
        return False
    if not isinstance(encoded_hash, str) or not encoded_hash:
        return False
    try:
        return bool(_password_hasher.verify(password, encoded_hash))
    except Exception:
        return False


def _token_digest(token: str) -> str:
    if not isinstance(token, str) or not 32 <= len(token) <= 256:
        raise ValueError("Invalid session token.")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(
    db: Session,
    user: User,
    lifetime: timedelta = DEFAULT_SESSION_LIFETIME,
    now: datetime | None = None,
) -> tuple[str, UserSession]:
    if not isinstance(db, Session):
        raise TypeError("db must be a SQLAlchemy Session.")
    if not isinstance(user, User) or not user.id:
        raise ValueError("A persistent user is required.")
    if not isinstance(lifetime, timedelta):
        raise TypeError("lifetime must be a timedelta.")
    if lifetime <= timedelta(0) or lifetime > MAX_SESSION_LIFETIME:
        raise ValueError("Session lifetime must be positive and at most 7 days.")

    now = _utc_now() if now is None else now
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware.")

    stored_user = db.get(User, user.id)
    if stored_user is None or not stored_user.is_active:
        raise ValueError("User does not exist or is inactive.")

    token = secrets.token_urlsafe(32)
    session = UserSession(
        user_id=stored_user.id,
        token_hash=_token_digest(token),
        created_at=_normalise_utc(now),
        expires_at=_normalise_utc(now + lifetime),
    )
    db.add(session)
    db.flush()
    return token, session


def get_session_user(
    db: Session,
    token: str,
    now: datetime | None = None,
) -> tuple[UserSession, User] | None:
    if not isinstance(db, Session):
        raise TypeError("db must be a SQLAlchemy Session.")
    try:
        digest = _token_digest(token)
    except ValueError:
        return None
    now = _utc_now() if now is None else now
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware.")
    now = _normalise_utc(now)

    session = db.scalar(
        select(UserSession).where(
            UserSession.token_hash == digest,
            UserSession.revoked_at.is_(None),
        )
    )
    if session is None:
        return None

    if _normalise_utc(session.expires_at) <= now:
        session.revoked_at = now
        db.flush()
        return None

    user = db.get(User, session.user_id)
    if user is None or not user.is_active:
        session.revoked_at = now
        db.flush()
        return None

    return session, user


def revoke_session(
    db: Session,
    token: str,
    now: datetime | None = None,
) -> bool:
    digest = _token_digest(token)
    now = _utc_now() if now is None else now
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware.")
    now = _normalise_utc(now)

    session = db.scalar(
        select(UserSession).where(
            UserSession.token_hash == digest,
            UserSession.revoked_at.is_(None),
        )
    )
    if session is None:
        return False

    session.revoked_at = now
    db.flush()
    return True


def revoke_all_user_sessions(
    db: Session,
    user_id: str,
    now: datetime | None = None,
) -> int:
    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("A valid user_id is required.")
    now = _utc_now() if now is None else now
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware.")
    now = _normalise_utc(now)

    sessions = list(
        db.scalars(
            select(UserSession).where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
            )
        )
    )
    for session in sessions:
        session.revoked_at = now

    db.flush()
    return len(sessions)
