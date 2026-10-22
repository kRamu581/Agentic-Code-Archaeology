import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import axios from "axios";
import "../App.css";
import "../styles/dashboard.css";
import AnalysisResult, { type AnalysisResultData } from "../components/AnalysisResult";
import LoadingIndicator from "../components/LoadingIndicator";
import { getApiError } from "../utils/apiError";

interface GitHubRepository {
  name: string;
  url: string;
  private: boolean;
}

const githubMessages: Record<string, string> = {
  access_denied: "GitHub access was denied. You can connect again whenever you are ready.",
  not_configured: "GitHub sign-in is not configured. Add the OAuth settings to the backend .env file.",
  invalid_callback: "GitHub returned an incomplete sign-in response. Please reconnect.",
  invalid_state: "GitHub sign-in expired or could not be verified. Please reconnect.",
  token_exchange: "GitHub did not authorize the connection. Please try again.",
  user_lookup: "GitHub authorization succeeded, but the account could not be verified.",
  connection_failed: "GitHub could not complete sign-in. Check your configuration and try again.",
};

function Dashboard() {
  const [searchParams] = useSearchParams();
  const [initialFeedback] = useState(() => {
    const initialParams = new URLSearchParams(window.location.search);
    const callbackError = initialParams.get("github_error");
    return {
      error: callbackError ? githubMessages[callbackError] || "GitHub sign-in failed. Please try again." : "",
      notice: initialParams.get("github") === "connected" ? "GitHub connected successfully." : "",
    };
  });
  const [githubUrl, setGithubUrl] = useState("");
  const [taskDescription, setTaskDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(
    () => Boolean(new URLSearchParams(window.location.search).get("analysis")),
  );
  const [result, setResult] = useState<AnalysisResultData | null>(null);
  const [repositories, setRepositories] = useState<GitHubRepository[]>([]);
  const [showRepos, setShowRepos] = useState(false);
  const [githubConnected, setGithubConnected] = useState(false);
  const [oauthConfigured, setOauthConfigured] = useState(false);
  const [error, setError] = useState(initialFeedback.error);
  const [notice, setNotice] = useState(initialFeedback.notice);

  useEffect(() => {
    const analysisId = searchParams.get("analysis");
    const params = new URLSearchParams(window.location.search);
    if (params.has("github") || params.has("github_error")) {
      const remaining = analysisId ? `?analysis=${encodeURIComponent(analysisId)}` : "";
      window.history.replaceState({}, document.title, `${window.location.pathname}${remaining}`);
    }
    axios.get("/api/github/status")
      .then(({ data }) => {
        setGithubConnected(data.connected);
        setOauthConfigured(data.oauth_configured);
      })
      .catch(() => setError("Could not check GitHub connection status."));
    if (analysisId) {
      axios.get(`/api/analysis-history/${encodeURIComponent(analysisId)}`)
        .then(({ data }) => setResult(data))
        .catch((loadError: unknown) => setError(getApiError(loadError, "Could not load the saved analysis.")))
        .finally(() => setHistoryLoading(false));
    }
  }, [searchParams]);

  const fetchRepositories = async () => {
    setHistoryLoading(true);
    setError("");
    try {
      const response = await axios.get<GitHubRepository[]>("/api/github/repositories");
      setRepositories(response.data);
      setShowRepos(true);
    } catch (fetchError: unknown) {
      if (axios.isAxiosError(fetchError) && fetchError.response?.status === 401) {
        setGithubConnected(false);
      }
      setError(getApiError(fetchError, "Could not fetch GitHub repositories."));
    } finally {
      setHistoryLoading(false);
    }
  };

  const disconnectGitHub = async () => {
    setError("");
    try {
      await axios.post("/api/github/logout");
      setGithubConnected(false);
      setRepositories([]);
      setShowRepos(false);
      setNotice("GitHub disconnected.");
    } catch (disconnectError: unknown) {
      setError(getApiError(disconnectError, "Could not disconnect GitHub."));
    }
  };

  const analyzeRepository = async () => {
    setError("");
    setNotice("");
    if (!githubUrl.trim()) {
      setError("Enter a GitHub repository URL to analyze.");
      return;
    }
    if (!/^https:\/\/github\.com\/[^/]+\/[^/]+\/?$/.test(githubUrl.trim().replace(/\.git$/, ""))) {
      setError("Use a repository URL in the form https://github.com/owner/repository.");
      return;
    }

    setLoading(true);
    setResult(null);
    try {
      const response = await axios.post<AnalysisResultData>(
        "/api/full-analysis",
        {
          github_url: githubUrl.trim(),
          ...(taskDescription.trim() ? { task_description: taskDescription.trim() } : {}),
        },
        { timeout: 180000 },
      );
      setResult(response.data);
    } catch (analysisError: unknown) {
      const fallback = axios.isAxiosError(analysisError) && analysisError.code === "ECONNABORTED"
        ? "Analysis timed out. Try a smaller repository or retry later."
        : "Repository analysis failed.";
      setError(getApiError(analysisError, fallback));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header>
        <h1>Agentic Code Archaeology</h1>
        <p>AI-powered repository intelligence</p>
      </header>
      <main>
        {error && <p className="error-message" role="alert">{error}</p>}
        {notice && <p className="success-message" role="status">{notice}</p>}
        {historyLoading && <LoadingIndicator>Loading saved analysis or GitHub data…</LoadingIndicator>}
        <div className="search-box">
          <input
            aria-label="GitHub repository URL"
            type="url"
            placeholder="Paste GitHub repository URL..."
            value={githubUrl}
            onChange={(event) => setGithubUrl(event.target.value)}
          />
          <button onClick={analyzeRepository} disabled={loading}>
            {loading ? "Analyzing repository…" : "Analyze Repository"}
          </button>
        </div>
        <label className="task-description">
          Optional task goal for scope analysis
          <textarea
            aria-label="Task goal"
            value={taskDescription}
            maxLength={4000}
            onChange={(event) => setTaskDescription(event.target.value)}
            placeholder="What was the developer trying to accomplish?"
          />
        </label>

        <section className="github-connect">
          <h2>GitHub repositories</h2>
          {githubConnected ? (
            <>
              <button onClick={fetchRepositories} disabled={historyLoading}>Load my repositories</button>
              <button onClick={disconnectGitHub} disabled={historyLoading}>Disconnect GitHub</button>
            </>
          ) : (
            <button
              onClick={() => window.location.assign("/api/github/login")}
              disabled={!oauthConfigured || historyLoading}
              title={!oauthConfigured ? "Configure GitHub OAuth credentials in the backend .env file first" : undefined}
            >
              Connect GitHub
            </button>
          )}
          {!oauthConfigured && <p>GitHub sign-in needs OAuth credentials in the backend .env file.</p>}
          {showRepos && (
            repositories.length
              ? <ul aria-label="GitHub repositories">
                  {repositories.map((repository) => (
                    <li key={repository.url}>
                      <button onClick={() => { setGithubUrl(repository.url); setShowRepos(false); }}>
                        {repository.name}{repository.private ? " (private)" : ""}
                      </button>
                    </li>
                  ))}
                </ul>
              : <p>No repositories were returned for this GitHub account.</p>
          )}
        </section>

        {loading && <LoadingIndicator>Cloning and analyzing repository… this may take a few minutes.</LoadingIndicator>}
        {result && <AnalysisResult result={result} />}
        <section className="project-recommendation">
          <h2>Compare recovery viability</h2>
          <p>Compare repository health, TODOs, and recovery potential using measured data.</p>
          <Link to="/compare">Compare My Projects</Link>
        </section>
      </main>
    </div>
  );
}

export default Dashboard;
