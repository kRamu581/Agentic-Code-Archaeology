# 🏺 Agentic Code Archaeology

**Agentic Code Archaeology** is an AI-powered, multi-agent system designed to reconstruct the intent behind legacy code, detect scope creep in commits, and evaluate the technical viability of recovering abandoned software projects.

Built with **LangGraph, FastAPI, and React**, this project moves beyond traditional Git tools by synthesizing commit history, structural code patches, and file dependency graphs to explain *why* code exists, not just *what* changed.

---

## 🌟 Key Features

1. **🧠 Intent Reconstruction (Intent Agent)**
   * Deduces the developer's original intent behind code changes using an Intent-Oriented Chain-of-Thought strategy.
   * Provides explicit evidence citations (referencing exact lines of code and commit SHAs) to prove its conclusions.

2. **⚠️ Scope Creep Detection (Scope Agent)**
   * Compares the stated goal of a commit against the actual structural code changes.
   * Flags unrelated file modifications and architectural deviations that fall outside the bounds of the original task.

3. **♻️ Abandoned Project Recovery (Recovery Agent)**
   * Analyzes incomplete or abandoned repositories to calculate a heuristic **Health Score**.
   * Replaces naive inactivity metrics (like commit frequency or stars) with deep structural indicators like code completeness, unresolved TODOs, and architectural continuity.
   * **Multi-Project Comparison:** Ranks multiple repositories to recommend which project holds the highest technical viability for completion.

4. **🕸️ Visual Relationship Graph**
   * Renders a physics-based, 2D force-directed graph connecting commits to their modified files, allowing developers to visually spot high-risk architectural bottlenecks.

5. **📊 Empirical Evaluation Suite (Research Ready)**
   * Includes a built-in evaluation framework for academic research.
   * Compares the Agentic System's accuracy against standard Git Baselines and zero-shot LLM Baselines.

---

## 🏗️ System Architecture

* **Backend:** FastAPI, Python, SQLite
* **AI Orchestration:** LangGraph (State-machine driven multi-agent workflow), Gemini API
* **Frontend:** React, Vite, CSS Grid, `react-force-graph-2d`

---

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* Node.js 18+
* A Gemini API key and explicitly selected model for optional live analysis

### 1. Backend Setup
```bash
cd backend
python -m venv venv

# Activate the virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt

# Create a .env file from ../.env.example and configure Gemini if needed
# Copy ../.env.example to ../.env; set GEMINI_API_KEY and GEMINI_MODEL for live use

# Start the FastAPI server
uvicorn main:app --reload
```
*The backend will run on `http://127.0.0.1:8000`*

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*The React dashboard will run on `http://localhost:5173`*

---

## 🧪 Running the Evaluation Suite (For Research)

The reproducible evaluator uses real pinned Git data and requires human labels
before scoring. Existing paper claims and illustrative datasets are not evidence.
See [the annotation guide](evaluation/ANNOTATION_GUIDE.md) for the exact labels,
case counts, baseline limitations, and live Gemini setup.

```bash
python -m pip install -r evaluation/requirements.txt
python -m pytest -q
python evaluation/runners/run_all.py --smoke
```

After annotation, run `python evaluation/runners/run_all.py`; add `--live` for
Gemini with `GEMINI_API_KEY` and `GEMINI_MODEL` configured. Missing ground truth
fails clearly. Smoke runs save raw predictions/timings and N/A research metrics.
Reports: `evaluation/reports/evaluation_report.md`; results: `evaluation/results/`.

---

## 📚 Academic Context & Related Work

This project builds upon active research in the field of LLM-driven software engineering, explicitly differentiating itself from and expanding upon architectures like:
* **Atomizer** (Zhu et al., 2026) and **ColaUntangle** (Hou et al., 2024) for intent-driven commit untangling.
* **VIC-RAGENT** (Chen et al., 2026) for multi-stage reasoning with specialized code analyst agents.
* Empirical investigations into open-source project survival (**Avelino et al., 2019**).

By combining intent extraction, scope detection, and viability scoring into a single agentic ecosystem, this project provides a holistic solution to repository comprehension.
