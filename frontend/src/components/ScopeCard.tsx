function ScopeCard({ analysis }: any) {
  if (!analysis) return null;

  return (
    <section className="card">
      <h2>⚠️ Scope Analysis</h2>
      
      {typeof analysis === 'string' ? (
        <p>{analysis}</p>
      ) : (
        <>
          <p>{analysis.summary}</p>
          <h3>Recommendation</h3>
          <p>{analysis.recommendation}</p>
        </>
      )}
    </section>
  );
}

export default ScopeCard;
