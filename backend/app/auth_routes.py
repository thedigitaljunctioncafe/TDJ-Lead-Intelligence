import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth_dependencies import SESSION_COOKIE_NAME, get_current_user
from .auth_service import (
    DEFAULT_SESSION_LIFETIME,
    create_session,
    hash_password,
    revoke_session,
    verify_password,
)
from .database import get_db
from .login_rate_limit import login_rate_limiter
from .models import User, Workspace, WorkspaceMembership
from .schemas import (
    AuthStatusRead,
    AuthUserRead,
    LoginRequest,
    WorkspaceMembershipRead,
)


router = APIRouter(prefix="/api/auth", tags=["Authentication"])

COOKIE_SECURE = os.getenv("TDJ_COOKIE_SECURE", "false").strip().lower() == "true"
COOKIE_SAMESITE = "lax"
COOKIE_PATH = "/"

# A dummy Argon2 hash helps reduce account-enumeration timing differences.
_DUMMY_PASSWORD_HASH = hash_password(
    "TDJ-Internal-Dummy-Password-Do-Not-Use-2026!"
)


def _client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _build_auth_user(db: Session, user: User) -> AuthUserRead:
    rows = db.execute(
        select(WorkspaceMembership, Workspace)
        .join(Workspace, Workspace.id == WorkspaceMembership.workspace_id)
        .where(
            WorkspaceMembership.user_id == user.id,
            Workspace.is_active.is_(True),
        )
        .order_by(Workspace.name)
    ).all()

    memberships = [
        WorkspaceMembershipRead(
            workspace_id=membership.workspace_id,
            workspace_name=workspace.name,
            workspace_slug=workspace.slug,
            role=membership.role,
        )
        for membership, workspace in rows
        if membership.role in {"owner", "admin", "manager", "member"}
    ]

    return AuthUserRead(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        memberships=memberships,
    )


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=int(DEFAULT_SESSION_LIFETIME.total_seconds()),
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path=COOKIE_PATH,
    )


@router.post("/login", response_model=AuthStatusRead)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    email = payload.email.strip().lower()
    ip_address = _client_ip(request)

    if not login_rate_limiter.is_allowed(ip_address, email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
            headers={"Retry-After": "900"},
        )

    user = db.scalar(
        select(User).where(User.email == email)
    )

    encoded_hash = (
        user.password_hash
        if user is not None and user.password_hash
        else _DUMMY_PASSWORD_HASH
    )

    password_valid = verify_password(payload.password, encoded_hash)

    if user is None or not user.is_active or not password_valid:
        login_rate_limiter.record_failure(ip_address, email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token, _session = create_session(db, user)

    # Do not issue the cookie until the session is committed successfully.
    db.commit()

    login_rate_limiter.record_success(ip_address, email)
    _set_session_cookie(response, token)
    response.headers["Cache-Control"] = "no-store"

    return AuthStatusRead(
        authenticated=True,
        user=_build_auth_user(db, user),
    )


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    token = request.cookies.get(SESSION_COOKIE_NAME)

    if token:
        try:
            revoked = revoke_session(db, token)
        except ValueError:
            revoked = False

        if revoked:
            db.commit()

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path=COOKIE_PATH,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )
    response.headers["Cache-Control"] = "no-store"

    return {"authenticated": False, "message": "Logged out."}


@router.get("/me", response_model=AuthStatusRead)
def current_user(
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"

    return AuthStatusRead(
        authenticated=True,
        user=_build_auth_user(db, user),
    )
