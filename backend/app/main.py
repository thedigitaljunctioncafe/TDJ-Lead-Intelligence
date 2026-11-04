import os
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Workspace, SearchJob, Entity, Lead, SourceRecord
from .schemas import SearchJobCreate, SearchJobRead, WorkspaceRead, DatabaseSummary

DEFAULT_WORKSPACE_SLUG = os.getenv("TDJ_DEFAULT_WORKSPACE_SLUG", "the-digital-junction")
with Session(engine) as bootstrap_db:
    workspace = bootstrap_db.scalar(select(Workspace).where(Workspace.slug == DEFAULT_WORKSPACE_SLUG))
    if workspace is None:
        bootstrap_db.add(Workspace(name="The Digital Junction", slug=DEFAULT_WORKSPACE_SLUG, workspace_type="organization"))
        bootstrap_db.commit()

app = FastAPI(
    title="TDJ Lead Intelligence API",
    version="0.2.0",
    description="Phase 2 multi-workspace data foundation. Discovery connectors are not enabled yet.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

@app.get("/health")
def health():
    return {"status": "ok", "application": "TDJ Lead Intelligence", "phase": 2}

@app.get("/api/workspaces", response_model=list[WorkspaceRead])
def list_workspaces(db: Session = Depends(get_db)):
    return list(db.scalars(select(Workspace).where(Workspace.is_active.is_(True)).order_by(Workspace.name)))

@app.get("/api/search-jobs", response_model=list[SearchJobRead])
def list_search_jobs(
    workspace_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    statement = select(SearchJob).order_by(SearchJob.id.desc()).limit(100)
    if workspace_id:
        statement = statement.where(SearchJob.workspace_id == workspace_id)
    return list(db.scalars(statement))

@app.post("/api/search-jobs", response_model=SearchJobRead, status_code=201)
def create_search_job(payload: SearchJobCreate, db: Session = Depends(get_db)):
    query = payload.query.strip()
    if len(query) < 3:
        raise HTTPException(status_code=422, detail="Query must contain at least 3 characters.")
    workspace = None
    if payload.workspace_id:
        workspace = db.get(Workspace, payload.workspace_id)
    else:
        workspace = db.scalar(select(Workspace).where(Workspace.slug == DEFAULT_WORKSPACE_SLUG))
    if workspace is None or not workspace.is_active:
        raise HTTPException(status_code=404, detail="Workspace not found or inactive.")
    job = SearchJob(workspace_id=workspace.id, query=query, location=payload.location.strip(), status="queued")
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@app.get("/api/admin/database-summary", response_model=DatabaseSummary)
def database_summary(db: Session = Depends(get_db)):
    # Local development diagnostics only. Protect this endpoint before any online deployment.
    return DatabaseSummary(
        workspace_count=db.scalar(select(func.count()).select_from(Workspace)) or 0,
        search_job_count=db.scalar(select(func.count()).select_from(SearchJob)) or 0,
        entity_count=db.scalar(select(func.count()).select_from(Entity)) or 0,
        lead_count=db.scalar(select(func.count()).select_from(Lead)) or 0,
        source_record_count=db.scalar(select(func.count()).select_from(SourceRecord)) or 0,
    )
