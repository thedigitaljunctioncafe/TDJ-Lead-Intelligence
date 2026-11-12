from getpass import getpass
import os
import re

from sqlalchemy import select, func

from .database import SessionLocal
from .models import User, Workspace, WorkspaceMembership
from .auth_service import hash_password


DEFAULT_WORKSPACE_SLUG = os.getenv(
    "TDJ_DEFAULT_WORKSPACE_SLUG",
    "the-digital-junction",
)


def main():
    print("\nTDJ LEAD INTELLIGENCE — FIRST OWNER SETUP")
    print("=" * 48)

    email = input("Owner email: ").strip().lower()
    if len(email) > 320 or not re.fullmatch(
        r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        email,
    ):
        raise SystemExit("Invalid email address.")

    display_name = input("Owner display name: ").strip()
    if not display_name or len(display_name) > 160:
        raise SystemExit("Display name must contain 1–160 characters.")

    password = getpass("Create password (minimum 12 characters): ")
    confirmation = getpass("Confirm password: ")

    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    password_hash = hash_password(password)

    with SessionLocal.begin() as db:
        user_count = db.scalar(select(func.count()).select_from(User)) or 0
        owner_count = db.scalar(
            select(func.count())
            .select_from(WorkspaceMembership)
            .where(WorkspaceMembership.role == "owner")
        ) or 0

        if user_count > 0 or owner_count > 0:
            raise SystemExit(
                "Bootstrap blocked: users or an owner already exist. "
                "No account was created."
            )

        workspace = db.scalar(
            select(Workspace).where(
                Workspace.slug == DEFAULT_WORKSPACE_SLUG,
                Workspace.is_active.is_(True),
            )
        )
        if workspace is None:
            raise SystemExit("Default active workspace was not found.")

        user = User(
            email=email,
            display_name=display_name,
            password_hash=password_hash,
            is_active=True,
        )
        db.add(user)
        db.flush()

        membership = WorkspaceMembership(
            workspace_id=workspace.id,
            user_id=user.id,
            role="owner",
        )
        db.add(membership)
        db.flush()

        created_user_id = user.id
        created_workspace_name = workspace.name

    print("\nOwner account created successfully.")
    print("Email:", email)
    print("Workspace:", created_workspace_name)
    print("Role: owner")
    print("User ID:", created_user_id)


if __name__ == "__main__":
    main()
