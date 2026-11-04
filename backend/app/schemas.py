from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class SearchJobCreate(BaseModel):
    query: str = Field(min_length=3, max_length=2000)
    location: str = Field(default="", max_length=250)
    workspace_id: str | None = None

class SearchJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    workspace_id: str
    query: str
    location: str
    status: str
    created_at: datetime

class WorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    slug: str
    workspace_type: str
    is_active: bool

class DatabaseSummary(BaseModel):
    workspace_count: int
    search_job_count: int
    entity_count: int
    lead_count: int
    source_record_count: int
