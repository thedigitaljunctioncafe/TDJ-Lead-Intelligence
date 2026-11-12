"""Workspace-scoped domain allowlist management."""

import ipaddress
import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import (
    User,
    Workspace,
    WorkspaceMembership,
    WorkspaceDomainAllowlist,
)


RESERVED_SUFFIXES = (
    ".localhost", ".local", ".internal", ".test",
    ".invalid", ".example", ".onion",
)

LABEL_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


def normalize_domain(domain: str) -> str:
    """Return a normalized DNS hostname, rejecting URLs and unsafe names."""
    if not isinstance(domain, str) or not domain.strip():
        raise ValueError("A non-empty domain is required")

    value = domain.strip()

    if any(char in value for char in "/\\?#@:*"):
        raise ValueError("Enter a hostname only, not a URL or wildcard")

    value = value.rstrip(".").lower()

    if not value or len(value) > 253:
        raise ValueError("Invalid domain length")

    try:
        value = value.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ValueError("Invalid international domain") from exc

    if len(value) > 253 or "." not in value:
        raise ValueError("A fully qualified domain name is required")

    if value == "localhost" or value.endswith(RESERVED_SUFFIXES):
        raise ValueError("Local or reserved domains are not permitted")

    try:
        ipaddress.ip_address(value)
    except ValueError:
        pass
    else:
        raise ValueError("IP addresses are not permitted as domains")

    labels = value.split(".")
    if any(
        not label or len(label) > 63 or not LABEL_PATTERN.fullmatch(label)
        for label in labels
    ):
        raise ValueError("Invalid DNS hostname")

    return value


def _now():
    return datetime.now(timezone.utc)


def _require_workspace(db: Session, workspace_id: str) -> Workspace:
    if not isinstance(db, Session):
        raise TypeError("db must be a SQLAlchemy Session")
    if not isinstance(workspace_id, str) or not workspace_id.strip():
        raise ValueError("workspace_id is required")

    workspace = db.get(Workspace, workspace_id)
    if workspace is None or not workspace.is_active:
        raise ValueError("Workspace does not exist or is inactive")
    return workspace


def _require_membership(
    db: Session,
    workspace_id: str,
    user_id: str,
    admin_only: bool,
) -> WorkspaceMembership:
    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("user_id is required")

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise PermissionError("Active user authorization required")

    membership = db.scalar(
        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == user_id,
        )
    )

    if membership is None:
        raise PermissionError("Workspace membership required")

    allowed = {"owner", "admin"} if admin_only else {
        "owner", "admin", "manager", "member"
    }

    if membership.role not in allowed:
        raise PermissionError("Insufficient workspace permissions")

    return membership


def approve_domain(
    db: Session,
    workspace_id: str,
    domain: str,
    approved_by_user_id: str,
) -> WorkspaceDomainAllowlist:
    """Approve or reactivate a domain. Caller owns transaction/commit."""
    _require_workspace(db, workspace_id)
    _require_membership(db, workspace_id, approved_by_user_id, admin_only=True)
    normalized = normalize_domain(domain)

    entry = db.scalar(
        select(WorkspaceDomainAllowlist).where(
            WorkspaceDomainAllowlist.workspace_id == workspace_id,
            WorkspaceDomainAllowlist.domain == normalized,
        )
    )

    if entry is None:
        entry = WorkspaceDomainAllowlist(
            workspace_id=workspace_id,
            domain=normalized,
            is_active=True,
            approved_by_user_id=approved_by_user_id,
            approved_at=_now(),
            revoked_at=None,
        )
        db.add(entry)
    elif not entry.is_active:
        entry.is_active = True
        entry.approved_by_user_id = approved_by_user_id
        entry.approved_at = _now()
        entry.revoked_at = None

    db.flush()
    return entry


def revoke_domain(
    db: Session,
    workspace_id: str,
    domain: str,
    revoked_by_user_id: str,
) -> WorkspaceDomainAllowlist:
    """Revoke an approved domain. Caller owns transaction/commit."""
    _require_workspace(db, workspace_id)
    _require_membership(db, workspace_id, revoked_by_user_id, admin_only=True)
    normalized = normalize_domain(domain)

    entry = db.scalar(
        select(WorkspaceDomainAllowlist).where(
            WorkspaceDomainAllowlist.workspace_id == workspace_id,
            WorkspaceDomainAllowlist.domain == normalized,
        )
    )

    if entry is None:
        raise ValueError("Domain is not registered in this workspace")

    if entry.is_active:
        entry.is_active = False
        entry.revoked_at = _now()

    db.flush()
    return entry


def list_approved_domains(
    db: Session,
    workspace_id: str,
    requested_by_user_id: str,
) -> list[WorkspaceDomainAllowlist]:
    """List active domains for an authorized workspace member."""
    _require_workspace(db, workspace_id)
    _require_membership(db, workspace_id, requested_by_user_id, admin_only=False)

    return list(
        db.scalars(
            select(WorkspaceDomainAllowlist)
            .where(
                WorkspaceDomainAllowlist.workspace_id == workspace_id,
                WorkspaceDomainAllowlist.is_active.is_(True),
            )
            .order_by(WorkspaceDomainAllowlist.domain)
        ).all()
    )
