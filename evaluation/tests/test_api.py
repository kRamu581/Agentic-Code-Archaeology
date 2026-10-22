import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
import main as api
from database import Base
from models.github_connection import GitHubConnection


@pytest.fixture(autouse=True)
def offline_environment(monkeypatch):
    monkeypatch.setenv("USE_GEMINI_ANALYSIS", "false")
    for key in (
        "GITHUB_CLIENT_ID",
        "GITHUB_CLIENT_SECRET",
        "GITHUB_SESSION_SECRET",
        "GITHUB_TOKEN_ENCRYPTION_KEY",
    ):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    testing_session = sessionmaker(autoflush=False, autocommit=False, bind=test_engine)

    def override_db():
        session = testing_session()
        try:
            yield session
        finally:
            session.close()

    api.app.dependency_overrides[api.get_db] = override_db
    with TestClient(api.app) as test_client:
        yield test_client
    api.app.dependency_overrides.clear()
    test_engine.dispose()


@pytest.fixture
def repository_data():
    commits = [
        {
            "hash": "abc1234",
            "message": "Add validation",
            "author": "QA Fixture",
            "date": "2026-10-14T10:00:00+00:00",
            "changed_files": ["src/main.py"],
            "diff": [{"file": "src/main.py", "diff": "+validate input"}],
        },
        {
            "hash": "def5678",
            "message": "Create project",
            "author": "QA Fixture",
            "date": "2026-10-13T10:00:00+00:00",
            "changed_files": ["src/main.py"],
            "diff": [],
        },
    ]
    return {
        "commit_count": 12,
        "file_count": 5,
        "todos": [{"file": "src/main.py", "line": 3, "content": "# TODO"}],
        "commit_history": commits,
        "file_histories": [{"file": "src/main.py", "introducing_commit": {"hash": "def5678", "message": "Create project"}}],
    }


def test_health_and_repository_validation(client):
    assert client.get("/").status_code == 200
    assert client.get("/github/status").json() == {
        "connected": False,
        "username": None,
        "oauth_configured": False,
    }
    assert client.get("/github/repositories").status_code == 401
    assert client.post("/analyze", json={"github_url": "https://example.com/a/b"}).status_code == 422
    assert client.get("/analysis-history").json() == []


def test_analyze_and_scope_routes(client, repository_data, monkeypatch):
    monkeypatch.setattr(api, "analyze_repository_data", lambda *args, **kwargs: repository_data)
    response = client.post("/analyze", json={"github_url": "https://github.com/demo/sample"})
    assert response.status_code == 200
    assert response.json()["repository_summary"] == {
        "total_commits": 12,
        "total_files": 5,
        "todo_count": 1,
    }
    scope_response = client.post(
        "/analyze-scope",
        json={"task_description": "Add validation", "changed_files": ["src/main.py"]},
    )
    assert scope_response.status_code == 200
    assert "INSUFFICIENT_EVIDENCE" in scope_response.json()["scope_analysis"]
    assert client.post("/analyze-scope", json={"task_description": "", "changed_files": []}).status_code == 422
    monkeypatch.setattr(
        api,
        "analyze_scope",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("google API 403 API key invalid")),
    )
    failed_scope = client.post(
        "/analyze-scope",
        json={"task_description": "Add validation", "changed_files": ["src/main.py"]},
    )
    assert failed_scope.status_code == 503
    assert "AI analysis service" in failed_scope.json()["detail"]


def test_full_analysis_is_persisted_and_reloadable(client, repository_data, monkeypatch):
    monkeypatch.setattr(api, "analyze_repository_data", lambda *args, **kwargs: repository_data)
    response = client.post(
        "/full-analysis",
        json={
            "github_url": "https://github.com/demo/sample",
            "task_description": "Add input validation",
        },
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["analysis_id"] > 0
    assert result["repository_graph"]["nodes"]
    assert "Scope analysis skipped" not in result["scope_analysis"]
    history = client.get("/analysis-history")
    assert len(history.json()) == 1
    assert history.json()[0]["github_url"] == "https://github.com/demo/sample"
    reloaded = client.get(f"/analysis-history/{result['analysis_id']}")
    assert reloaded.status_code == 200
    assert reloaded.json() == result
    assert client.get("/analysis-history/9999").status_code == 404


def test_recommend_and_compare_routes(client, repository_data, monkeypatch):
    recommendation = client.post(
        "/recommend-project",
        json={"projects": [
            {"name": "Old", "completion_level": 30, "todo_count": 15, "activity_score": 10},
            {"name": "Active", "completion_level": 80, "todo_count": 2, "activity_score": 90},
        ]},
    )
    assert recommendation.status_code == 200
    assert recommendation.json()["recommended_project"]["name"] == "Active"
    assert client.post("/recommend-project", json={"projects": []}).status_code == 422

    def analyze(url, **kwargs):
        if url.endswith("/missing"):
            raise ValueError("repository not found")
        return repository_data

    monkeypatch.setattr(api, "analyze_repository_data", analyze)
    response = client.post(
        "/compare-repositories",
        json={"repositories": [
            "https://github.com/demo/active",
            "https://github.com/demo/missing",
        ]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["repositories"][0]["todo_count"] == 1
    assert body["repositories"][1]["status"] == "error"
    assert body["recommended_repository"]["repository"].endswith("/active")
    assert client.post(
        "/compare-repositories",
        json={"repositories": ["https://github.com/demo/one"]},
    ).status_code == 422
    assert client.post(
        "/compare-repositories",
        json={"repositories": ["https://github.com/demo/one", "https://github.com/demo/one.git"]},
    ).status_code == 422


def test_repository_errors_are_actionable():
    assert api._repository_error(ValueError("empty repository, no commits")).status_code == 422
    assert api._repository_error(ValueError("repository not found")).status_code == 404
    assert api._repository_error(TimeoutError("operation timed out")).status_code == 504


def test_analysis_failures_return_clear_status_and_do_not_save(client, monkeypatch):
    monkeypatch.setattr(
        api,
        "analyze_repository_data",
        lambda *args, **kwargs: (_ for _ in ()).throw(TimeoutError("clone timed out")),
    )
    response = client.post(
        "/full-analysis",
        json={"github_url": "https://github.com/demo/sample"},
    )
    assert response.status_code == 504
    assert "smaller repository" in response.json()["detail"]
    assert client.get("/analysis-history").json() == []

    monkeypatch.setattr(api, "analyze_repository_data", lambda *args, **kwargs: {
        "commit_history": [],
        "file_histories": [],
        "commit_count": 0,
        "file_count": 0,
        "todos": [],
    })
    empty_repository = client.post(
        "/full-analysis",
        json={"github_url": "https://github.com/demo/empty"},
    )
    assert empty_repository.status_code == 422

    monkeypatch.setattr(
        api,
        "analyze_repository_data",
        lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("Repository exceeds the 10000-file analysis limit.")),
    )
    large_repository = client.post(
        "/full-analysis",
        json={"github_url": "https://github.com/demo/large"},
    )
    assert large_repository.status_code == 413
    assert "too large" in large_repository.json()["detail"]

    monkeypatch.setattr(
        api,
        "analyze_repository_data",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("Authentication failed")),
    )
    private = client.post(
        "/full-analysis",
        json={"github_url": "https://github.com/demo/private"},
    )
    assert private.status_code == 404
    assert "connect GitHub" in private.json()["detail"]


def test_ai_rate_limit_is_user_facing_and_not_persisted(client, repository_data, monkeypatch):
    monkeypatch.setattr(api, "analyze_repository_data", lambda *args, **kwargs: repository_data)
    monkeypatch.setattr(
        api.agent_workflow,
        "invoke",
        lambda state: (_ for _ in ()).throw(RuntimeError("429 RESOURCE_EXHAUSTED")),
    )
    response = client.post(
        "/full-analysis",
        json={"github_url": "https://github.com/demo/sample"},
    )
    assert response.status_code == 503
    assert "rate-limited" in response.json()["detail"]
    assert client.get("/analysis-history").json() == []


def test_github_oauth_encrypts_token_and_disconnects(client, monkeypatch):
    monkeypatch.setenv("GITHUB_CLIENT_ID", "test-client")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("GITHUB_SESSION_SECRET", "test-session-secret-with-at-least-32-chars")
    monkeypatch.setenv("GITHUB_TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode("ascii"))

    def mocked_post(*args, **kwargs):
        return httpx.Response(
            200,
            json={"access_token": "test-access-token", "scope": "repo"},
            request=httpx.Request("POST", args[0]),
        )

    def mocked_get(url, **kwargs):
        if url.endswith("/user"):
            data = {"login": "demo-user"}
        else:
            data = [{
                "full_name": "demo/private-repo",
                "html_url": "https://github.com/demo/private-repo",
                "private": True,
                "default_branch": "main",
            }]
        return httpx.Response(200, json=data, request=httpx.Request("GET", url))

    monkeypatch.setattr(api.httpx, "post", mocked_post)
    monkeypatch.setattr(api.httpx, "get", mocked_get)
    login = client.get("/github/login", follow_redirects=False)
    assert login.status_code == 302
    assert "https://github.com/login/oauth/authorize" in login.headers["location"]
    state = parse_qs(urlparse(login.headers["location"]).query)["state"][0]

    callback = client.get(
        "/github/callback",
        params={"code": "temporary-code", "state": state},
        follow_redirects=False,
    )
    assert callback.status_code == 303
    assert callback.headers["location"].endswith("/?github=connected")
    repositories = client.get("/github/repositories")
    assert repositories.json()[0]["private"] is True
    assert "test-access-token" not in repositories.text

    session = client.cookies.get(api.SESSION_COOKIE)
    db_generator = client.app.dependency_overrides[api.get_db]()
    db = next(db_generator)
    try:
        saved = db.get(GitHubConnection, session)
        assert saved.username == "demo-user"
        assert saved.encrypted_token != "test-access-token"
        assert api.decrypt_token(saved.encrypted_token) == "test-access-token"
    finally:
        db_generator.close()

    def expired_token(*args, **kwargs):
        return httpx.Response(
            401,
            json={"message": "Bad credentials"},
            request=httpx.Request("GET", args[0]),
        )

    monkeypatch.setattr(api.httpx, "get", expired_token)
    expired = client.get("/github/repositories")
    assert expired.status_code == 401
    assert "expired" in expired.json()["detail"]
    assert client.get("/github/status").json()["connected"] is False

    disconnected = client.post("/github/logout")
    assert disconnected.json() == {"connected": False}
    assert client.get("/github/status").json()["connected"] is False

    monkeypatch.setattr(api.httpx, "get", mocked_get)
    reconnect = client.get("/github/login", follow_redirects=False)
    reconnect_state = parse_qs(urlparse(reconnect.headers["location"]).query)["state"][0]
    reconnected = client.get(
        "/github/callback",
        params={"code": "second-code", "state": reconnect_state},
        follow_redirects=False,
    )
    assert reconnected.headers["location"].endswith("/?github=connected")
    assert client.get("/github/status").json()["connected"] is True


def test_github_callback_rejects_invalid_state_without_exchanging_code(client, monkeypatch):
    monkeypatch.setenv("GITHUB_CLIENT_ID", "test-client")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("GITHUB_SESSION_SECRET", "test-session-secret-with-at-least-32-chars")
    monkeypatch.setenv("GITHUB_TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode("ascii"))
    post_calls = []
    monkeypatch.setattr(api.httpx, "post", lambda *args, **kwargs: post_calls.append(args))

    client.get("/github/login", follow_redirects=False)
    response = client.get(
        "/github/callback",
        params={"code": "sensitive-test-code", "state": "not-a-valid-signed-state"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"].endswith("/?github_error=invalid_state")
    assert "sensitive-test-code" not in response.text
    assert "test-access-token" not in response.text
    assert "Traceback" not in response.text
    assert post_calls == []
    assert client.get("/github/status").json()["connected"] is False


def test_github_callback_rejects_expired_state_without_exchanging_code(client, monkeypatch):
    monkeypatch.setenv("GITHUB_CLIENT_ID", "test-client")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("GITHUB_SESSION_SECRET", "test-session-secret-with-at-least-32-chars")
    monkeypatch.setenv("GITHUB_TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode("ascii"))
    monkeypatch.setattr(api, "OAUTH_STATE_MAX_AGE", -1)
    post_calls = []
    monkeypatch.setattr(api.httpx, "post", lambda *args, **kwargs: post_calls.append(args))

    login = client.get("/github/login", follow_redirects=False)
    response = client.get(
        "/github/callback",
        params={
            "code": "sensitive-test-code",
            "state": parse_qs(urlparse(login.headers["location"]).query)["state"][0],
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"].endswith("/?github_error=invalid_state")
    assert "sensitive-test-code" not in response.text
    assert "test-access-token" not in response.text
    assert "Traceback" not in response.text
    assert post_calls == []
    assert client.get("/github/status").json()["connected"] is False


def test_github_callback_rejects_missing_state_without_exchanging_code(client, monkeypatch):
    monkeypatch.setenv("GITHUB_CLIENT_ID", "test-client")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("GITHUB_SESSION_SECRET", "test-session-secret-with-at-least-32-chars")
    monkeypatch.setenv("GITHUB_TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode("ascii"))
    post_calls = []
    monkeypatch.setattr(api.httpx, "post", lambda *args, **kwargs: post_calls.append(args))

    response = client.get(
        "/github/callback",
        params={"code": "sensitive-test-code"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"].endswith("/?github_error=invalid_callback")
    assert "sensitive-test-code" not in response.text
    assert "test-access-token" not in response.text
    assert "Traceback" not in response.text
    assert post_calls == []
    assert client.get("/github/status").json()["connected"] is False


def test_github_denial_and_unconfigured_login(client, monkeypatch):
    denied = client.get("/github/callback?error=access_denied", follow_redirects=False)
    assert denied.status_code == 303
    assert denied.headers["location"].endswith("/?github_error=access_denied")
    login = client.get("/github/login")
    assert login.status_code == 503
