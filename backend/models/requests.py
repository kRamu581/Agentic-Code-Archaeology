from pydantic import BaseModel, HttpUrl
from typing import Optional


class RepositoryRequest(BaseModel):
    github_url: HttpUrl


class ScopeRequest(BaseModel):
    task_description: str
    changed_files: list[str]


class UnifiedAnalysisRequest(BaseModel):
    github_url: HttpUrl
    task_description: Optional[str] = None
    changed_files: Optional[list[str]] = None

class ProjectComparisonRequest(BaseModel):
    projects: list

class RepositoryComparisonRequest(BaseModel):
    repositories: list[str]
