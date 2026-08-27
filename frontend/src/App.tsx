import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";
import Compare from "./pages/Compare";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <nav style={{ padding: "10px", background: "#333", display: "flex", gap: "20px" }}>
        <Link to="/" style={{ color: "white", textDecoration: "none" }}>Dashboard</Link>
        <Link to="/history" style={{ color: "white", textDecoration: "none" }}>History</Link>
        <Link to="/compare" style={{ color: "white", textDecoration: "none" }}>Compare</Link>
      </nav>

      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/history" element={<History />} />
        <Route path="/compare" element={<Compare />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
