import json
import matplotlib.pyplot as plt
import os

def main():
    # Load metrics
    metrics_path = "../../evaluation/results/metrics.json"
    if not os.path.exists(metrics_path):
        print("Metrics file not found. Please run run_evaluation.py first.")
        return

    with open(metrics_path, "r", encoding="utf-8") as file:
        metrics = json.load(file)

    # 1. Accuracy Comparison
    methods = [
        "Git Baseline",
        "Basic LLM",
        "Agentic System"
    ]
    
    accuracy = [
        metrics.get("git_accuracy", 0),
        metrics.get("llm_accuracy", 0),
        metrics.get("agent_accuracy", 0)
    ]

    plt.figure(figsize=(8, 5))
    plt.bar(methods, accuracy, color=['#cccccc', '#888888', '#2196F3'])
    plt.title("Intent Reconstruction Accuracy Comparison")
    plt.xlabel("Method")
    plt.ylabel("Accuracy (%)")
    plt.ylim(0, 100)
    
    os.makedirs("../../evaluation/results", exist_ok=True)
    plt.savefig("../../evaluation/results/accuracy_comparison.png")
    print("Saved accuracy_comparison.png")

    # 2. Evidence Support Chart
    plt.figure(figsize=(6, 5))
    plt.bar(["Agentic System"], [metrics.get("evidence_score", 0)], color='#4CAF50')
    plt.title("Evidence Support Score")
    plt.ylabel("Supported Predictions (%)")
    plt.ylim(0, 100)
    plt.savefig("../../evaluation/results/evidence_support.png")
    print("Saved evidence_support.png")

    # 3. Scope Detection Comparison (Placeholder for now)
    scope_metrics = {
        "precision": 0.0,
        "recall": 0.0,
        "f1_score": 0.0
    }
    
    scope_values = [
        scope_metrics["precision"] * 100,
        scope_metrics["recall"] * 100,
        scope_metrics["f1_score"] * 100
    ]

    plt.figure(figsize=(8, 5))
    plt.bar(["Precision", "Recall", "F1 Score"], scope_values, color=['#FF9800', '#FF5722', '#F44336'])
    plt.title("Scope Creep Detection Performance")
    plt.ylabel("Score (%)")
    plt.ylim(0, 100)
    plt.savefig("../../evaluation/results/scope_metrics.png")
    print("Saved scope_metrics.png")

    print("All charts generated successfully in evaluation/results/")

if __name__ == "__main__":
    main()
