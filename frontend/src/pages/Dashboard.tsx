import { useState } from "react";
import axios from "axios";
import "../App.css";
import "../styles/dashboard.css";
import RepositoryGraph from "../components/RepositoryGraph";
import HealthScoreCard from "../components/HealthScoreCard";
import IntentCard from "../components/IntentCard";
import ScopeCard from "../components/ScopeCard";
import RecoveryCard from "../components/RecoveryCard";

function Dashboard() {
  const [githubUrl, setGithubUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const [repositories, setRepositories] = useState<any[]>([]);
  const [showRepos, setShowRepos] = useState(false);
  
  const [recommendation, setRecommendation] = useState<any>(null);

  const handleProjectRecommendation = async () => {
    try {
      const response = await axios.post("http://127.0.0.1:8000/recommend-project", {
        projects: [
          {
            "name": "Campus Asset Management",
            "completion_level": 85,
            "todo_count": 4,
            "activity_score": 60
          },
          {
            "name": "E-Commerce Application",
            "completion_level": 40,
            "todo_count": 20,
            "activity_score": 30
          },
          {
            "name": "Internship Finder",
            "completion_level": 70,
            "todo_count": 8,
            "activity_score": 50
          }
        ]
      });
      setRecommendation(response.data);
    } catch (error) {
      console.error(error);
      alert("Error getting recommendation");
    }
  };

  const fetchRepositories = async () => {
    try {
      const response = await axios.get("http://127.0.0.1:8000/github/repositories");
      setRepositories(response.data);
      setShowRepos(true);
    } catch (error) {
      console.error(error);
      alert("Error fetching repositories");
    }
  };

  const selectRepository = (url: string) => {
    setGithubUrl(url);
    setShowRepos(false);
  };

  const analyzeRepository = async () => {
    if (!githubUrl) {
      alert("Please enter a GitHub repository URL");
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/full-analysis",
        {
          github_url: githubUrl
        }
      );

      setResult(response.data);
    } catch (error) {
      console.error(error);
      alert("Error analyzing repository");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header>
        <h1>🔍 Agentic Code Archaeology</h1>
        <p>AI-powered repository intelligence</p>
      </header>

      <main>
        <div className="search-box">
          <input
            type="text"
            placeholder="Paste GitHub repository URL..."
            value={githubUrl}
            onChange={(e) => setGithubUrl(e.target.value)}
          />

          <button onClick={analyzeRepository} disabled={loading}>
            {loading ? "Analyzing..." : "Analyze Repository"}
          </button>
        </div>
        <div style={{ textAlign: "center", margin: "15px 0" }}>
          <span>OR</span>
        </div>
        <div style={{ textAlign: "center", marginBottom: "30px" }}>
          <button onClick={fetchRepositories} style={{ background: "#333", color: "white", padding: "10px 20px", borderRadius: "5px", border: "none", cursor: "pointer" }}>
            Connect GitHub
          </button>
        </div>

        {showRepos && (
          <div style={{ background: "#1a1a1a", padding: "20px", borderRadius: "8px", marginBottom: "30px" }}>
            <h3>My Repositories</h3>
            <ul style={{ listStyle: "none", padding: 0 }}>
              {repositories.map((repo, idx) => (
                <li key={idx} style={{ margin: "10px 0" }}>
                  <button 
                    onClick={() => selectRepository(repo.url)}
                    style={{ background: "none", border: "1px solid #444", padding: "10px", width: "100%", textAlign: "left", color: "white", cursor: "pointer", borderRadius: "4px" }}
                  >
                    ☐ {repo.name}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {result && (
          <div className="dashboard">
            <div className="dashboard-grid">
              <HealthScoreCard
                score={result.health_score}
                metrics={result.health_metrics || {
                  git_activity: 0,
                  code_completeness: 0,
                  recovery_potential: 0
                }}
              />
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

            <section className="final-report" style={{ marginTop: "30px" }}>
              <h2>🤖 Final AI Recommendation</h2>
              <div className="final-report-card">
                {result.final_report || "No final report available"}
              </div>
            </section>
          </div>
        )}

        <section style={{ marginTop: "50px", borderTop: "1px solid #444", paddingTop: "30px", textAlign: "left" }}>
          <h2>♻️ Project Recovery Recommendation</h2>
          
          <button onClick={handleProjectRecommendation} style={{ background: "#4CAF50", color: "white", padding: "10px 20px", borderRadius: "5px", border: "none", cursor: "pointer", marginBottom: "20px" }}>
            Compare My Projects
          </button>

          {recommendation && (
            <div style={{ background: "#1a1a1a", padding: "20px", borderRadius: "8px" }}>
              <h3>
                Recommended Project: {recommendation.recommended_project?.name}
              </h3>
              <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
                {recommendation.ai_recommendation}
              </pre>
            </div>
          )}
        </section>

      </main>
    </div>
  );
}

export default Dashboard;
