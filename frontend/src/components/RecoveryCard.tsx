function RecoveryCard({ analysis }: any) {
  if (!analysis) return null;

  return (
    <section className="card">
      <h2>♻️ Project Recovery</h2>
      <p style={{ whiteSpace: "pre-wrap" }}>
        {analysis.summary || analysis}
      </p>
    </section>
  );
}

export default RecoveryCard;
