import { useEffect, useState } from "react";
import axios from "axios";
import AnalysisResult, { type AnalysisResultData } from "../components/AnalysisResult";
import LoadingIndicator from "../components/LoadingIndicator";
import { getApiError } from "../utils/apiError";

interface HistoryEntry {
  id: number;
  github_url: string;
  created_at: string | null;
  status: string;
  final_report: string | null;
}

function repositoryName(url: string) {
  return url.replace(/\/+$/, "").replace(/\.git$/i, "").split("/").slice(-2).join("/");
}

function History() {
  const [analyses, setAnalyses] = useState<HistoryEntry[]>([]);
  const [selected, setSelected] = useState<AnalysisResultData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedLoading, setSelectedLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    axios.get<HistoryEntry[]>("/api/analysis-history")
      .then(({ data }) => setAnalyses(data))
      .catch((fetchError: unknown) => setError(getApiError(fetchError, "The saved data could not be loaded.")))
      .finally(() => setLoading(false));
  }, []);

  const openSavedAnalysis = async (id: number) => {
    setError("");
    setSelectedLoading(true);
    try {
      const response = await axios.get<AnalysisResultData>(`/api/analysis-history/${id}`);
      setSelected(response.data);
    } catch (fetchError: unknown) {
      setError(getApiError(fetchError, "The saved data could not be loaded."));
    } finally {
      setSelectedLoading(false);
    }
  };

  return (
    <main className="history-container">
      <h1>Analysis History</h1>
      {error && <p className="error-message" role="alert">{error}</p>}
      {loading && <LoadingIndicator>Loading history…</LoadingIndicator>}
      {!loading && !error && analyses.length === 0 && <p>No repository analyses yet.</p>}
      {!loading && analyses.map((analysis) => (
        <article className="history-card" key={analysis.id}>
          <h2>{repositoryName(analysis.github_url)}</h2>
          <p><strong>Repository:</strong> {analysis.github_url}</p>
          <p>
            <strong>Analyzed:</strong>{" "}
            {analysis.created_at ? new Date(analysis.created_at).toLocaleString() : "Date unavailable"}
          </p>
          <p><strong>Status:</strong> {analysis.status}</p>
          <button onClick={() => openSavedAnalysis(analysis.id)} disabled={selectedLoading}>
            {selectedLoading && selected?.analysis_id === analysis.id ? "Loading saved result…" : "View saved analysis"}
          </button>
        </article>
      ))}
      {selectedLoading && <LoadingIndicator>Loading saved result…</LoadingIndicator>}
      {selected && <AnalysisResult result={selected} />}
    </main>
  );
}

export default History;
