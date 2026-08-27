import { useEffect, useState } from "react";
import axios from "axios";

function History() {
  const [analyses, setAnalyses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await axios.get(
          "http://127.0.0.1:8000/analysis-history"
        );

        setAnalyses(response.data);
      } catch (error) {
        console.error("Error loading history:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  if (loading) {
    return <h2>Loading history...</h2>;
  }

  return (
    <div className="history-container">
      <h1>Analysis History</h1>

      {analyses.length === 0 ? (
        <p>No repository analyses yet.</p>
      ) : (
        analyses.map((analysis) => (
          <div className="history-card" key={analysis.id}>
            <h3>Repository Analysis #{analysis.id}</h3>

            <p>
              <strong>Repository:</strong>
              <br />
              {analysis.github_url}
            </p>

            <p>
              <strong>Analyzed:</strong>
              <br />
              {new Date(analysis.created_at).toLocaleString()}
            </p>

            <details>
              <summary>View Final Report</summary>

              <div className="history-report">
                {analysis.final_report}
              </div>
            </details>
          </div>
        ))
      )}
    </div>
  );
}

export default History;
