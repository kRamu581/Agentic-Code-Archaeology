from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, HttpUrl, field_validator


def validate_github_repository_url(value: HttpUrl) -> HttpUrl:
    parsed = urlparse(str(value))
    path_parts = [part for part in parsed.path.split("/") if part]
    if (
        parsed.hostname != "github.com"
        or parsed.username
        or parsed.password
        or len(path_parts) != 2
    ):
        raise ValueError("Enter a GitHub repository URL in the form https://github.com/owner/repository")
    path_parts[-1] = path_parts[-1].removesuffix(".git")
    if not all(path_parts):
        raise ValueError("Enter a GitHub repository URL in the form https://github.com/owner/repository")
    return value


class RepositoryRequest(BaseModel):
    github_url: HttpUrl

    @field_validator("github_url")
    @classmethod
    def validate_repository(cls, value: HttpUrl) -> HttpUrl:
        return validate_github_repository_url(value)


class ScopeRequest(BaseModel):
    task_description: str = Field(min_length=1, max_length=4000)
    changed_files: list[str] = Field(min_length=1, max_length=100)


class UnifiedAnalysisRequest(BaseModel):
    github_url: HttpUrl
    task_description: Optional[str] = Field(default=None, max_length=4000)
    changed_files: Optional[list[str]] = Field(default=None, max_length=100)

    @field_validator("github_url")
    @classmethod
    def validate_repository(cls, value: HttpUrl) -> HttpUrl:
        return validate_github_repository_url(value)


class ProjectMetrics(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    completion_level: float = Field(ge=0, le=100)
    todo_count: int = Field(ge=0)
    activity_score: float = Field(ge=0, le=100)
    recovery_potential: float = Field(default=50, ge=0, le=100)

class ProjectComparisonRequest(BaseModel):
    projects: list[ProjectMetrics] = Field(min_length=1, max_length=20)

class RepositoryComparisonRequest(BaseModel):
    repositories: list[HttpUrl] = Field(min_length=2, max_length=10)

    @field_validator("repositories")
    @classmethod
    def validate_repositories(cls, values: list[HttpUrl]) -> list[HttpUrl]:
        normalized = []
        for value in values:
            validate_github_repository_url(value)
            parsed = urlparse(str(value))
            owner, name = [part for part in parsed.path.split("/") if part]
            normalized.append(f"{owner.casefold()}/{name.removesuffix('.git').casefold()}")
        if len(normalized) != len(set(normalized)):
            raise ValueError("The same repository cannot be compared more than once")
        return values
