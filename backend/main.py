from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from pathlib import Path
import os
import secrets
from urllib.parse import urlencode
import httpx
from itsdangerous import BadSignature, SignatureExpired

# Load the project-level configuration regardless of where Uvicorn is started.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# The local development sandbox can inherit an unusable loopback proxy.  Clear
# it for Git and Gemini requests made by this backend process.
for proxy_variable in (
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
    "http_proxy", "https_proxy", "all_proxy"
):
    os.environ.pop(proxy_variable, None)

import json
from sqlalchemy.orm import Session
from database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from models.requests import RepositoryRequest, ScopeRequest, UnifiedAnalysisRequest, ProjectComparisonRequest, RepositoryComparisonRequest
from services.repository_analyzer import analyze_repository_data, create_evidence_map
from services.health_score import calculate_health_score, calculate_health_metrics
from services.repository_graph import build_repository_graph
from services.project_recommender import rank_projects

from agents.intent_agent import analyze_intent
from agents.scope_agent import analyze_scope
from agents.recovery_agent import analyze_recovery
from agents.report_agent import generate_final_report
from agents.recommendation_agent import recommend_project

from graph.workflow import agent_workflow

from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from models.analysis import RepositoryAnalysis
from models.github_connection import GitHubConnection
from services.github_oauth import (
    SESSION_COOKIE,
    OAUTH_STATE_MAX_AGE,
    decrypt_token,
    encrypt_token,
    oauth_configuration,
    oauth_is_configured,
    state_serializer,
)
from sqlalchemy import inspect, text

Base.metadata.create_all(
    bind=engine
)

if "result_data" not in {
    column["name"] for column in inspect(engine).get_columns("repository_analyses")
}:
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE repository_analyses ADD COLUMN result_data TEXT"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "message": "Agentic Code Archaeology Backend is Running"
    }

def _session_cookie(response: Response, session_id: str, *, delete: bool = False) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        session_id,
        httponly=True,
        secure=os.getenv("APP_ENV", "development").lower() == "production",
        samesite="lax",
        path="/",
        max_age=0 if delete else 60 * 60 * 24 * 30,
    )


def _github_connection(request: Request, db: Session) -> GitHubConnection | None:
    session_id = request.cookies.get(SESSION_COOKIE)
    return db.get(GitHubConnection, session_id) if session_id else None


def _github_token(request: Request, db: Session) -> str | None:
    connection = _github_connection(request, db)
    if not connection:
        return None
    try:
        return decrypt_token(connection.encrypted_token)
    except ValueError as error:
        db.delete(connection)
        db.commit()
        raise HTTPException(status_code=401, detail=str(error)) from error


@app.get("/github/status")
def github_status(request: Request, db: Session = Depends(get_db)):
    connection = _github_connection(request, db)
    return {
        "connected": connection is not None,
        "username": connection.username if connection else None,
        "oauth_configured": oauth_is_configured(),
    }


@app.get("/github/login")
def github_login(response: Response):
    if not oauth_is_configured():
        raise HTTPException(
            status_code=503,
            detail="GitHub sign-in is not configured. Set the GitHub OAuth values in the backend .env file.",
        )
    config = oauth_configuration()
    session_id = secrets.token_urlsafe(32)
    state = state_serializer().dumps({"session_id": session_id, "nonce": secrets.token_urlsafe(24)})
    authorize_url = "https://github.com/login/oauth/authorize?" + urlencode({
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "scope": "repo",
        "state": state,
    })
    redirect = RedirectResponse(authorize_url, status_code=302)
    _session_cookie(redirect, session_id)
    return redirect


@app.get("/github/callback")
def github_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    config = oauth_configuration()
    frontend = config["frontend_url"].rstrip("/")
    if error:
        return RedirectResponse(f"{frontend}/?github_error=access_denied", status_code=303)
    if not oauth_is_configured():
        return RedirectResponse(f"{frontend}/?github_error=not_configured", status_code=303)
    if not code or not state:
        return RedirectResponse(f"{frontend}/?github_error=invalid_callback", status_code=303)
    try:
        state_data = state_serializer().loads(state, max_age=OAUTH_STATE_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return RedirectResponse(f"{frontend}/?github_error=invalid_state", status_code=303)
    session_id = request.cookies.get(SESSION_COOKIE)
    if not session_id or state_data.get("session_id") != session_id:
        return RedirectResponse(f"{frontend}/?github_error=invalid_state", status_code=303)

    try:
        token_response = httpx.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
                "code": code,
                "redirect_uri": config["redirect_uri"],
            },
            timeout=15,
        )
        token_response.raise_for_status()
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return RedirectResponse(f"{frontend}/?github_error=token_exchange", status_code=303)
        user_response = httpx.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=15,
        )
        user_response.raise_for_status()
        username = user_response.json().get("login")
        if not username:
            return RedirectResponse(f"{frontend}/?github_error=user_lookup", status_code=303)
        connection = db.get(GitHubConnection, session_id)
        if connection is None:
            connection = GitHubConnection(session_id=session_id, username=username)
        connection.username = username
        connection.encrypted_token = encrypt_token(access_token)
        connection.scopes = token_data.get("scope", "")
        db.add(connection)
        db.commit()
    except (httpx.HTTPError, ValueError):
        db.rollback()
        return RedirectResponse(f"{frontend}/?github_error=connection_failed", status_code=303)

    return RedirectResponse(f"{frontend}/?github=connected", status_code=303)


@app.post("/github/logout")
def github_logout(request: Request, response: Response, db: Session = Depends(get_db)):
    connection = _github_connection(request, db)
    if connection:
        db.delete(connection)
        db.commit()
    _session_cookie(response, "", delete=True)
    return {"connected": False}


@app.get("/github/repositories")
def get_github_repositories(request: Request, db: Session = Depends(get_db)):
    connection = _github_connection(request, db)
    token = _github_token(request, db)
    if not token:
        raise HTTPException(status_code=401, detail="Connect your GitHub account to list repositories.")
    repositories = []
    page = 1
    while True:
        try:
            result = httpx.get(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                params={"per_page": 100, "page": page, "sort": "updated"},
                timeout=15,
            )
            if result.status_code == 401:
                if connection:
                    db.delete(connection)
                    db.commit()
                raise HTTPException(status_code=401, detail="Your GitHub authorization expired. Please reconnect.")
            result.raise_for_status()
            items = result.json()
        except httpx.HTTPError as error:
            raise HTTPException(status_code=502, detail="GitHub could not return your repositories. Try again shortly.") from error
        repositories.extend({
            "name": item["full_name"],
            "url": item["html_url"],
            "private": item["private"],
            "default_branch": item["default_branch"],
        } for item in items if item.get("full_name") and item.get("html_url"))
        if len(items) < 100:
            break
        page += 1
    return repositories


def _is_ai_service_error(message: str) -> bool:
    return any(
        marker in message
        for marker in (
            "gemini",
            "google",
            "rate limit",
            "resource_exhausted",
            "quota",
            "429",
            "permission_denied",
            "permission denied",
            "invalid api key",
        )
    )


def _repository_error(error: Exception) -> HTTPException:
    message = str(error).lower()
    if "analysis limit" in message or "exceeds the" in message or "larger than" in message:
        return HTTPException(
            status_code=413,
            detail="This repository is too large for the demo analyzer. Choose a smaller repository.",
        )
    if "no commits" in message:
        return HTTPException(status_code=422, detail="This repository has no commits to analyze yet.")
    if "timed out" in message or "timeout" in message:
        return HTTPException(status_code=504, detail="Repository analysis timed out. Try a smaller repository.")
    if _is_ai_service_error(message):
        return HTTPException(
            status_code=503,
            detail="The AI analysis service is unavailable or rate-limited. Try again later.",
        )
    if "authentication" in message or "not found" in message or "repository not found" in message:
        return HTTPException(
            status_code=404,
            detail="Repository was not found or is private. Check the URL, or connect GitHub for private-repository access.",
        )
    return HTTPException(
        status_code=502,
        detail="GitHub could not provide this repository. Check the URL and your network, then try again.",
    )


def _repository_data(github_url: str, auth_token: str | None = None) -> dict:
    try:
        data = analyze_repository_data(github_url, auth_token=auth_token)
        if not data["commit_history"]:
            raise ValueError("The repository has no commits yet.")
        return data
    except HTTPException:
        raise
    except Exception as error:
        raise _repository_error(error) from error


def _analyze_repository(repository: RepositoryRequest, auth_token: str | None = None):
    data = _repository_data(str(repository.github_url), auth_token=auth_token)
    try:
        intent_analysis = None
        if data["commit_history"]:
            evidence_map = create_evidence_map(
                data["commit_history"][0],
                data["file_histories"]
            )
            intent_analysis = analyze_intent(
                data["commit_history"][0],
                data["file_histories"],
                evidence_map
            )
            
        repository_data = {
            "total_commits": data["commit_count"],
            "total_files": data["file_count"],
            "todo_count": len(data["todos"]),
            "recent_commits": data["commit_history"]
        }
        
        recovery_analysis = analyze_recovery(repository_data)

        return {
            "message": "Repository analyzed successfully",
            "repository_summary": {
                "total_commits": data["commit_count"],
                "total_files": data["file_count"],
                "todo_count": len(data["todos"])
            },
            "recent_commits": data["commit_history"],
            "todos": data["todos"][:20],
            "file_histories": data["file_histories"],
            "intent_analysis": intent_analysis,
            "recovery_analysis": recovery_analysis
        }
        
    except HTTPException:
        raise
    except Exception as error:
        raise _repository_error(error) from error


@app.post("/analyze")
def analyze_repository(
    repository: RepositoryRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    return _analyze_repository(repository, _github_token(request, db))

@app.post("/analyze-scope")
def analyze_scope_creep(request: ScopeRequest):
    try:
        result = analyze_scope(
            request.task_description,
            request.changed_files
        )
    except Exception as error:
        failure = _repository_error(error)
        if failure.status_code in (503, 504):
            raise failure from error
        raise HTTPException(
            status_code=500,
            detail="Scope analysis could not be completed. Please retry.",
        ) from error

    return {
        "task": request.task_description,
        "changed_files": request.changed_files,
        "scope_analysis": result
    }

@app.post("/full-analysis")
def full_analysis(
    request: UnifiedAnalysisRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    try:
        data = _repository_data(str(request.github_url), _github_token(http_request, db))
        commit_history = data["commit_history"]
        file_histories = data["file_histories"]
        repository_summary = {
            "total_commits": data["commit_count"],
            "total_files": data["file_count"],
            "todo_count": len(data["todos"]),
        }
        evidence_map = (
            create_evidence_map(commit_history[0], file_histories)
            if commit_history else []
        )
        changed_files = request.changed_files
        if request.task_description and not changed_files and commit_history:
            changed_files = commit_history[0].get("changed_files", [])

        initial_state = {
            "repository_summary": repository_summary,
            "commit_history": commit_history,
            "file_histories": file_histories,
            "evidence_map": evidence_map,
            "task_description": request.task_description,
            "changed_files": changed_files,
            "intent_analysis": None,
            "scope_analysis": None,
            "recovery_analysis": None,
            "final_report": None
        }

        final_state = agent_workflow.invoke(initial_state)

        intent_analysis = final_state["intent_analysis"]
        scope_analysis = final_state["scope_analysis"]
        recovery_analysis = final_state["recovery_analysis"]
        final_report = final_state["final_report"]

        health_score = calculate_health_score(
            repository_summary,
            intent_analysis,
            recovery_analysis
        )

        health_metrics = calculate_health_metrics(
            repository_summary,
            recovery_analysis
        )

        repository_graph = build_repository_graph(
            commit_history
        )

        result = {
            "repository": str(request.github_url),
            "health_score": health_score,
            "health_metrics": health_metrics,
            "repository_graph": repository_graph,
            "intent_analysis": intent_analysis,
            "file_histories": file_histories,
            "recovery_analysis": recovery_analysis,
            "scope_analysis": scope_analysis,
            "repository_summary": repository_summary,
            "final_report": final_report,
        }
        new_analysis = RepositoryAnalysis(
            github_url=str(request.github_url),
            repository_summary=json.dumps(repository_summary),
            intent_analysis=json.dumps(intent_analysis) if isinstance(intent_analysis, dict) else intent_analysis,
            scope_analysis=scope_analysis,
            recovery_analysis=recovery_analysis,
            final_report=final_report
        )

        db.add(new_analysis)
        db.flush()
        result["analysis_id"] = new_analysis.id
        new_analysis.result_data = json.dumps(result)
        db.commit()
        db.refresh(new_analysis)

        return result
    except HTTPException:
        raise
    except Exception as error:
        db.rollback()
        message = str(error).lower()
        if _is_ai_service_error(message):
            raise HTTPException(
                status_code=503,
                detail="The AI analysis service is unavailable or rate-limited. Try again later.",
            ) from error
        if "timed out" in message or "timeout" in message:
            raise HTTPException(
                status_code=504,
                detail="Analysis timed out. Try a smaller repository or retry later.",
            ) from error
        raise HTTPException(
            status_code=500,
            detail="Analysis could not be completed and no result was saved. Please retry.",
        ) from error

@app.post("/recommend-project")
def recommend_project_api(
    request: ProjectComparisonRequest
):
    ranked_projects = rank_projects([project.model_dump() for project in request.projects])
    try:
        ai_recommendation = recommend_project(ranked_projects)
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail="Project ranking succeeded, but the AI explanation service is unavailable.",
        ) from error

    return {
        "recommended_project":
            ranked_projects[0]
            if ranked_projects
            else None,
        "rankings":
            ranked_projects,
        "ai_recommendation":
            ai_recommendation
    }

@app.post("/compare-repositories")
def compare_repositories(
    request: RepositoryComparisonRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    token = _github_token(http_request, db)
    comparison_results = []
    for github_url in request.repositories:
        url = str(github_url)
        try:
            repo_data = analyze_repository_data(url, auth_token=token)
            summary = {
                "total_commits": repo_data["commit_count"],
                "total_files": repo_data["file_count"],
                "todo_count": len(repo_data["todos"]),
            }
            recovery = analyze_recovery({
                "repository_summary": summary,
                "recent_commits": repo_data["commit_history"],
            })
            metrics = calculate_health_metrics(summary, recovery)
            comparison_results.append({
                "repository": url,
                "repository_name": url.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git"),
                "status": "complete",
                "todo_count": summary["todo_count"],
                "repository_summary": summary,
                "health_score": calculate_health_score(summary, None, recovery),
                "metrics": metrics,
                "recovery_analysis": recovery,
            })
        except Exception as error:
            failed = _repository_error(error)
            comparison_results.append({
                "repository": url,
                "repository_name": url.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git"),
                "status": "error",
                "error": failed.detail,
            })

    ranked = sorted(
        (item for item in comparison_results if item["status"] == "complete"),
        key=lambda item: (-item["health_score"], item["repository"].casefold()),
    )
    return {
        "repositories": comparison_results,
        "rankings": ranked,
        "recommended_repository": ranked[0] if ranked else None,
    }

@app.get("/analysis-history")
def get_analysis_history(
    db: Session = Depends(get_db)
):
    analyses = (
        db.query(RepositoryAnalysis)
        .order_by(
            RepositoryAnalysis.created_at.desc()
        )
        .all()
    )

    return [{
        "id": item.id,
        "github_url": item.github_url,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "status": "complete",
        "final_report": item.final_report,
    } for item in analyses]


@app.get("/analysis-history/{analysis_id}")
def get_saved_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
):
    analysis = db.get(RepositoryAnalysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Saved analysis was not found.")
    if analysis.result_data:
        return json.loads(analysis.result_data)
    return {
        "analysis_id": analysis.id,
        "repository": analysis.github_url,
        "repository_summary": json.loads(analysis.repository_summary) if analysis.repository_summary else None,
        "intent_analysis": json.loads(analysis.intent_analysis) if analysis.intent_analysis else None,
        "scope_analysis": analysis.scope_analysis,
        "recovery_analysis": analysis.recovery_analysis,
        "final_report": analysis.final_report,
        "legacy_record": True,
    }
