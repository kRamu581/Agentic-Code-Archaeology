interface HealthScoreCardProps {
  score: number;
  metrics: {
    git_activity: number;
    code_completeness: number;
    recovery_potential: number;
  };
}

function HealthScoreCard({
  score,
  metrics
}: HealthScoreCardProps) {
  return (
    <section className="card">
      <h2>Repository Health</h2>
      <h1>{score}/100</h1>
      <div>
        <p>Git Activity: {metrics.git_activity}/100</p>
        <p>Code Completeness: {metrics.code_completeness}/100</p>
        <p>Recovery Potential: {metrics.recovery_potential}/100</p>
      </div>
    </section>
  );
}

export default HealthScoreCard;
