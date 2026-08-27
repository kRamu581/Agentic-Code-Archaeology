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
* **AI Orchestration:** LangGraph (State-machine driven multi-agent workflow), OpenAI API
* **Frontend:** React, Vite, CSS Grid, `react-force-graph-2d`

---

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* Node.js 18+
* An OpenAI API Key

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

# Create a .env file and add your OpenAI API Key
echo "OPENAI_API_KEY=your_actual_key_here" > .env

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

To reproduce the accuracy metrics and generate matplotlib charts for the baseline comparisons:

```bash
cd evaluation/baselines
python run_evaluation.py
python ../metrics.py
python ../generate_report.py
```
*Results and charts will be saved to `evaluation/results/`.*

---

## 📚 Academic Context & Related Work

This project builds upon active research in the field of LLM-driven software engineering, explicitly differentiating itself from and expanding upon architectures like:
* **Atomizer** (Zhu et al., 2026) and **ColaUntangle** (Hou et al., 2024) for intent-driven commit untangling.
* **VIC-RAGENT** (Chen et al., 2026) for multi-stage reasoning with specialized code analyst agents.
* Empirical investigations into open-source project survival (**Avelino et al., 2019**).

By combining intent extraction, scope detection, and viability scoring into a single agentic ecosystem, this project provides a holistic solution to repository comprehension.
