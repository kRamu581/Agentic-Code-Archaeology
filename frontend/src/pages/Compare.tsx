import { useState } from "react";
import axios from "axios";

function Compare() {
  const [repositories, setRepositories] = useState([
    "",
    ""
  ]);

  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const updateRepository = (
    index: number,
    value: string
  ) => {
    const updated = [...repositories];
    updated[index] = value;
    setRepositories(updated);
  };

  const addRepository = () => {
    setRepositories([
      ...repositories,
      ""
    ]);
  };

  const compareRepositories = async () => {
    const validRepositories =
      repositories.filter(
        (repo) => repo.trim() !== ""
      );

    if (validRepositories.length < 2) {
      alert(
        "Please enter at least two repositories."
      );
      return;
    }

    try {
      setLoading(true);

      const response = await axios.post(
        "http://127.0.0.1:8000/compare-repositories",
        {
          repositories: validRepositories
        }
      );

      setResults(
        response.data.repositories
      );

    } catch (error) {
      console.error(
        "Comparison failed:",
        error
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="compare-container" style={{ padding: "40px", maxWidth: "900px", margin: "0 auto", textAlign: "left" }}>
      <h1>Repository Comparison</h1>
      <p style={{ color: "#aaa", marginBottom: "30px" }}>
        Compare multiple repositories and identify the strongest project.
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "20px" }}>
        {repositories.map(
          (repository, index) => (
            <input
              key={index}
              type="text"
              placeholder="GitHub repository URL"
              value={repository}
              onChange={(event) =>
                updateRepository(
                  index,
                  event.target.value
                )
              }
              style={{ padding: "12px", width: "100%", borderRadius: "4px", border: "1px solid #444", background: "#222", color: "white" }}
            />
          )
        )}
      </div>

      <div style={{ display: "flex", gap: "10px", marginBottom: "40px" }}>
        <button onClick={addRepository} style={{ background: "#444", color: "white", padding: "10px 20px", borderRadius: "5px", border: "none", cursor: "pointer" }}>
          + Add Repository
        </button>

        <button
          onClick={compareRepositories}
          disabled={loading}
          style={{ background: "#4CAF50", color: "white", padding: "10px 20px", borderRadius: "5px", border: "none", cursor: loading ? "not-allowed" : "pointer" }}
        >
          {loading
            ? "Analyzing..."
            : "Compare Projects"}
        </button>
      </div>

      {results.length > 0 && (
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", background: "#1a1a1a", borderRadius: "8px", overflow: "hidden" }}>
            <thead style={{ background: "#333", textAlign: "left" }}>
              <tr>
                <th style={{ padding: "15px" }}>Repository</th>
                <th style={{ padding: "15px" }}>Health Score</th>
                <th style={{ padding: "15px" }}>Git Activity</th>
                <th style={{ padding: "15px" }}>Completeness</th>
                <th style={{ padding: "15px" }}>Recovery Potential</th>
              </tr>
            </thead>
            <tbody>
              {results.map(
                (result, index) => (
                  <tr key={index} style={{ borderBottom: "1px solid #333" }}>
                    <td style={{ padding: "15px" }}>
                      {result.repository}
                    </td>
                    <td style={{ padding: "15px", color: "#4CAF50", fontWeight: "bold" }}>
                      {result.health_score}/100
                    </td>
                    <td style={{ padding: "15px" }}>
                      {result.metrics.git_activity}/100
                    </td>
                    <td style={{ padding: "15px" }}>
                      {result.metrics.code_completeness}/100
                    </td>
                    <td style={{ padding: "15px" }}>
                      {result.metrics.recovery_potential}/100
                    </td>
                  </tr>
                )
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default Compare;
