from fastapi import FastAPI, HTTPException, Depends
from dotenv import load_dotenv
load_dotenv()

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

Base.metadata.create_all(
    bind=engine
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "message": "Agentic Code Archaeology Backend is Running"
    }

@app.get("/github/repositories")
def get_github_repositories():
    # Mock repositories list for Phase 3 - Step 29
    return [
        {"name": "Project A", "url": "https://github.com/user/project-a"},
        {"name": "Campus Asset Management", "url": "https://github.com/user/campus-asset-management"},
        {"name": "E-commerce App", "url": "https://github.com/user/ecommerce-app"},
        {"name": "Old Portfolio Project", "url": "https://github.com/user/old-portfolio"}
    ]

@app.post("/analyze")
def analyze_repository(repository: RepositoryRequest):
    try:
        data = analyze_repository_data(str(repository.github_url))
        
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
        
    except Exception as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "clone" in error_msg or "cmd('git') failed" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="Unable to analyze this repository. Please check that the repository is public and the URL is correct."
            )
        raise HTTPException(
            status_code=500,
            detail="An error occurred during AI analysis or database connection."
        )

@app.post("/analyze-scope")
def analyze_scope_creep(request: ScopeRequest):
    result = analyze_scope(
        request.task_description,
        request.changed_files
    )

    return {
        "task": request.task_description,
        "changed_files": request.changed_files,
        "scope_analysis": result
    }

@app.post("/full-analysis")
def full_analysis(
    request: UnifiedAnalysisRequest,
    db: Session = Depends(get_db)
):
    try:
        # First analyze repository
        repo_result = analyze_repository(
            RepositoryRequest(
                github_url=request.github_url
            )
        )

        commit_history = repo_result.get("recent_commits", [])
        file_histories = repo_result.get("file_histories", [])
        evidence_map = []
        
        if commit_history:
            evidence_map = create_evidence_map(commit_history[0], file_histories)

        initial_state = {
            "repository_summary": repo_result.get("repository_summary"),
            "commit_history": commit_history,
            "file_histories": file_histories,
            "evidence_map": evidence_map,
            "task_description": request.task_description,
            "changed_files": request.changed_files,
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
            repo_result.get("repository_summary", {}),
            intent_analysis,
            recovery_analysis
        )

        health_metrics = calculate_health_metrics(
            repo_result.get("repository_summary", {}),
            recovery_analysis
        )

        repository_graph = build_repository_graph(
            repo_result.get("recent_commits", [])
        )

        new_analysis = RepositoryAnalysis(
            github_url=str(request.github_url),
            repository_summary=json.dumps(
                repo_result.get("repository_summary")
            ),
            intent_analysis=json.dumps(intent_analysis) if isinstance(intent_analysis, dict) else intent_analysis,
            scope_analysis=scope_analysis,
            recovery_analysis=recovery_analysis,
            final_report=final_report
        )

        db.add(new_analysis)
        db.commit()
        db.refresh(new_analysis)

        return {
            "repository": str(request.github_url),
            "analysis_id": new_analysis.id,
            "health_score": health_score,
            "health_metrics": health_metrics,
            "repository_graph": repository_graph,
            "intent_analysis": intent_analysis,
            "file_histories": repo_result.get("file_histories"),
            "recovery_analysis": recovery_analysis,
            "scope_analysis": scope_analysis,
            "repository_summary": repo_result.get("repository_summary"),
            "final_report": final_report
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during full analysis processing: {str(e)}"
        )

@app.post("/recommend-project")
def recommend_project_api(
    request: ProjectComparisonRequest
):
    ranked_projects = rank_projects(
        request.projects
    )

    ai_recommendation = recommend_project(
        ranked_projects
    )

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
    request: RepositoryComparisonRequest
):
    try:
        comparison_results = []

        for github_url in request.repositories:
            repo_result = analyze_repository_data(github_url)
            
            recovery_analysis = analyze_recovery(repo_result)

            health_score = calculate_health_score(
                repo_result["repository_summary"],
                None,
                recovery_analysis
            )

            health_metrics = calculate_health_metrics(
                repo_result["repository_summary"],
                recovery_analysis
            )

            comparison_results.append({
                "repository": github_url,
                "health_score": health_score,
                "metrics": health_metrics,
                "recovery_analysis": recovery_analysis
            })

        return {
            "repositories": comparison_results
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Comparison failed: {str(e)}"
        )

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

    return analyses
