import os

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import engine, get_db
from .models import (
    Workspace,
    WorkspaceMembership,
    SearchJob,
    Entity,
    Lead,
    SourceRecord,
)
from .schemas import (
    SearchJobCreate,
    SearchJobRead,
    WorkspaceRead,
    DatabaseSummary,
)
from .auth_routes import router as auth_router
from .auth_dependencies import (
    get_current_user,
    get_workspace_membership,
    require_workspace_roles,
)

DEFAULT_WORKSPACE_SLUG = os.getenv(
    "TDJ_DEFAULT_WORKSPACE_SLUG",
    "the-digital-junction",
)

with Session(engine) as bootstrap_db:
    workspace = bootstrap_db.scalar(
        select(Workspace).where(Workspace.slug == DEFAULT_WORKSPACE_SLUG)
    )
    if workspace is None:
        bootstrap_db.add(
            Workspace(
                name="The Digital Junction",
                slug=DEFAULT_WORKSPACE_SLUG,
                workspace_type="organization",
            )
        )
        bootstrap_db.commit()


app = FastAPI(
    title="TDJ Lead Intelligence API",
    version="0.2.0",
    description="Multi-workspace lead intelligence API with authentication.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)

app.include_router(auth_router)


def resolve_user_workspace(
    db: Session,
    user,
    requested_workspace_id: str | None,
):
    if requested_workspace_id:
        return get_workspace_membership(
            db,
            user,
            requested_workspace_id,
        )

    memberships = list(
        db.scalars(
            select(WorkspaceMembership)
            .join(
                Workspace,
                Workspace.id == WorkspaceMembership.workspace_id,
            )
            .where(
                WorkspaceMembership.user_id == user.id,
                Workspace.is_active.is_(True),
            )
        )
    )

    if not memberships:
        raise HTTPException(
            status_code=403,
            detail="No active workspace membership.",
        )

    if len(memberships) != 1:
        raise HTTPException(
            status_code=422,
            detail="Please specify a workspace_id.",
        )

    return get_workspace_membership(
        db,
        user,
        memberships[0].workspace_id,
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "application": "TDJ Lead Intelligence",
        "phase": 2,
    }


@app.get("/api/workspaces", response_model=list[WorkspaceRead])
def list_workspaces(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    statement = (
        select(Workspace)
        .join(
            WorkspaceMembership,
            WorkspaceMembership.workspace_id == Workspace.id,
        )
        .where(
            WorkspaceMembership.user_id == user.id,
            Workspace.is_active.is_(True),
        )
        .order_by(Workspace.name)
    )

    return list(db.scalars(statement))


@app.get("/api/search-jobs", response_model=list[SearchJobRead])
def list_search_jobs(
    workspace_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _, workspace = resolve_user_workspace(
        db,
        user,
        workspace_id,
    )

    statement = (
        select(SearchJob)
        .where(SearchJob.workspace_id == workspace.id)
        .order_by(SearchJob.id.desc())
        .limit(100)
    )

    return list(db.scalars(statement))


@app.post(
    "/api/search-jobs",
    response_model=SearchJobRead,
    status_code=201,
)
def create_search_job(
    payload: SearchJobCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    query = payload.query.strip()

    if len(query) < 3:
        raise HTTPException(
            status_code=422,
            detail="Query must contain at least 3 characters.",
        )

    _, workspace = resolve_user_workspace(
        db,
        user,
        payload.workspace_id,
    )

    job = SearchJob(
        workspace_id=workspace.id,
        requested_by_user_id=user.id,
        query=query,
        location=payload.location.strip(),
        status="queued",
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


@app.get(
    "/api/admin/database-summary",
    response_model=DatabaseSummary,
)
def database_summary(
    workspace_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    membership, workspace = resolve_user_workspace(
        db,
        user,
        workspace_id,
    )

    require_workspace_roles(
        membership,
        {"owner", "admin"},
    )

    def count_for_workspace(model):
        return (
            db.scalar(
                select(func.count())
                .select_from(model)
                .where(model.workspace_id == workspace.id)
            )
            or 0
        )

    return DatabaseSummary(
        workspace_count=1,
        search_job_count=count_for_workspace(SearchJob),
        entity_count=count_for_workspace(Entity),
        lead_count=count_for_workspace(Lead),
        source_record_count=count_for_workspace(SourceRecord),
    )
