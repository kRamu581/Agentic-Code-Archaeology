import { useState } from "react";
import axios from "axios";
import LoadingIndicator from "../components/LoadingIndicator";
import { getApiError } from "../utils/apiError";

interface ComparedRepository {
  repository: string;
  repository_name: string;
  status: "complete" | "error";
  error?: string;
  health_score?: number;
  todo_count?: number;
  metrics?: {
    git_activity: number;
    code_completeness: number;
    recovery_potential: number;
  };
}

interface ComparisonResponse {
  repositories: ComparedRepository[];
  rankings: ComparedRepository[];
  recommended_repository: ComparedRepository | null;
}

function normalizeRepositoryUrl(value: string) {
  return value.trim().replace(/\/+$/, "").replace(/\.git$/i, "").toLocaleLowerCase();
}

function Compare() {
  const [repositories, setRepositories] = useState(["", ""]);
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const updateRepository = (index: number, value: string) => {
    setRepositories((current) => current.map((item, position) => position === index ? value : item));
  };

  const compareRepositories = async () => {
    setError("");
    setComparison(null);
    const validRepositories = repositories.map((repo) => repo.trim()).filter(Boolean);
    if (validRepositories.length < 2) {
      setError("Enter at least two GitHub repository URLs to compare.");
      return;
    }
    const normalized = validRepositories.map(normalizeRepositoryUrl);
    if (new Set(normalized).size !== normalized.length) {
      setError("The same repository was entered more than once. Use distinct repositories.");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post<ComparisonResponse>(
        "/api/compare-repositories",
        { repositories: validRepositories },
        { timeout: 180000 },
      );
      setComparison(response.data);
      if (!response.data.rankings.length) {
        setError("No repositories could be analyzed. Check the URLs and access permissions.");
      } else if (response.data.repositories.some((repository) => repository.status === "error")) {
        setError("Some repositories could not be analyzed. Successful repositories are still ranked below.");
      }
    } catch (compareError: unknown) {
      setError(getApiError(compareError, "Repository comparison failed. Please try again."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="compare-container">
      <h1>Repository Comparison</h1>
      <p>Compare real repository health, TODO counts, activity, and recovery potential.</p>
      {error && <p className="error-message" role="alert">{error}</p>}

      <div className="repository-inputs">
        {repositories.map((repository, index) => (
          <label key={index}>
            Repository {index + 1}
            <input
              aria-label={`Repository ${index + 1}`}
              type="url"
              placeholder="https://github.com/owner/repository"
              value={repository}
              onChange={(event) => updateRepository(index, event.target.value)}
            />
          </label>
        ))}
      </div>
      <div className="comparison-actions">
        <button onClick={() => setRepositories((current) => [...current, ""])} disabled={loading || repositories.length >= 10}>
          + Add Repository
        </button>
        <button onClick={compareRepositories} disabled={loading}>
          {loading ? "Analyzing repositories…" : "Compare Projects"}
        </button>
      </div>
      {loading && <LoadingIndicator>Analyzing each repository; this may take a few minutes…</LoadingIndicator>}

      {comparison?.recommended_repository && (
        <section className="recommendation" aria-label="Recommended repository">
          <h2>Highest measured viability</h2>
          <p>{comparison.recommended_repository.repository_name}</p>
          <p>Health score: {comparison.recommended_repository.health_score}/100</p>
        </section>
      )}
      {comparison && (
        <div className="comparison-table-wrap">
          <table>
            <thead>
              <tr>
                <th>Repository</th>
                <th>Status</th>
                <th>Health Score</th>
                <th>TODOs</th>
                <th>Git Activity</th>
                <th>Code Completeness</th>
                <th>Recovery Potential</th>
              </tr>
            </thead>
            <tbody>
              {comparison.repositories.map((repository) => (
                <tr key={repository.repository}>
                  <td>{repository.repository_name}</td>
                  <td>{repository.status === "complete" ? "Complete" : repository.error}</td>
                  <td>{repository.health_score ?? "N/A"}{repository.health_score !== undefined ? "/100" : ""}</td>
                  <td>{repository.todo_count ?? "N/A"}</td>
                  <td>{repository.metrics?.git_activity ?? "N/A"}{repository.metrics ? "/100" : ""}</td>
                  <td>{repository.metrics?.code_completeness ?? "N/A"}{repository.metrics ? "/100" : ""}</td>
                  <td>{repository.metrics?.recovery_potential ?? "N/A"}{repository.metrics ? "/100" : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}

export default Compare;
