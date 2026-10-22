import RepositoryGraph from "./RepositoryGraph";
import HealthScoreCard from "./HealthScoreCard";
import IntentCard from "./IntentCard";
import ScopeCard from "./ScopeCard";
import RecoveryCard from "./RecoveryCard";

export interface AnalysisResultData {
  analysis_id?: number;
  repository?: string;
  health_score?: number;
  health_metrics?: {
    git_activity: number;
    code_completeness: number;
    recovery_potential: number;
  };
  repository_graph?: {
    nodes: { id: string; label: string; type: string; message?: string }[];
    edges: { source: string; target: string }[];
  };
  intent_analysis?: unknown;
  scope_analysis?: unknown;
  recovery_analysis?: unknown;
  final_report?: string;
}

export default function AnalysisResult({ result }: { result: AnalysisResultData }) {
  return (
    <section className="dashboard" aria-label="Repository analysis results">
      <h2>Analysis: {result.repository}</h2>
      <div className="dashboard-grid">
        {result.health_score !== undefined && result.health_metrics && (
          <HealthScoreCard score={result.health_score} metrics={result.health_metrics} />
        )}
        <IntentCard analysis={result.intent_analysis} />
        <ScopeCard analysis={result.scope_analysis} />
        <RecoveryCard analysis={result.recovery_analysis} />
      </div>
      {result.repository_graph && (
        <section className="graph-section">
          <h2>Repository Relationship Graph</h2>
          <RepositoryGraph graphData={result.repository_graph} />
        </section>
      )}
      <section className="final-report">
        <h2>Final Analysis Report</h2>
        <div className="final-report-card">
          {result.final_report || "No final report was saved."}
        </div>
      </section>
    </section>
  );
}
