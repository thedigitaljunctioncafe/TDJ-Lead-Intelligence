from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth_service import get_session_user
from .database import get_db
from .models import User, Workspace, WorkspaceMembership


SESSION_COOKIE_NAME = "tdj_session"

VALID_ROLES = {"owner", "admin", "manager", "member"}


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    token = request.cookies.get(SESSION_COOKIE_NAME)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    result = get_session_user(db, token)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session.",
        )

    _, user = result
    return user


def get_workspace_membership(
    db: Session,
    user: User,
    workspace_id: str,
) -> tuple[WorkspaceMembership, Workspace]:
    membership = db.scalar(
        select(WorkspaceMembership).where(
            WorkspaceMembership.user_id == user.id,
            WorkspaceMembership.workspace_id == workspace_id,
        )
    )

    if membership is None or membership.role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace access denied.",
        )

    workspace = db.get(Workspace, workspace_id)

    if workspace is None or not workspace.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found or inactive.",
        )

    return membership, workspace


def require_workspace_roles(
    membership: WorkspaceMembership,
    allowed_roles: set[str],
) -> None:
    if not allowed_roles or not allowed_roles.issubset(VALID_ROLES):
        raise ValueError("Invalid allowed role configuration.")

    if membership.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient workspace permissions.",
        )
