function IntentCard({ analysis }: any) {
  if (!analysis) return null;

  return (
    <section className="card">
      <h2>🧠 Code Intent Analysis</h2>
      <h3>Likely Intent</h3>
      <p>{analysis.likely_intent || (typeof analysis === 'string' ? analysis : "No intent found")}</p>
      
      {analysis.confidence && (
        <>
          <h3>Confidence</h3>
          <p>{analysis.confidence}</p>
        </>
      )}

      {analysis.evidence && analysis.evidence.length > 0 && (
        <>
          <h3>Evidence</h3>
          {analysis.evidence.map((item: any, index: number) => (
            <div key={index} style={{ marginBottom: "10px", background: "#333", padding: "10px", borderRadius: "4px" }}>
              <strong>{item.reference || item.id}</strong>
              <p style={{ margin: "5px 0 0 0" }}>{item.reason || item.description}</p>
            </div>
          ))}
        </>
      )}
    </section>
  );
}

export default IntentCard;
