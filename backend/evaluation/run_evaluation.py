import json
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from baselines.git_baseline import git_baseline
from baselines.llm_baseline import llm_baseline
from baselines.agentic_system import agentic_system

def load_dataset():
    filepath = "../../evaluation/dataset/intent_examples.json"
    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)

def main():
    dataset = load_dataset()
    results = []

    for item in dataset:
        print(f"Testing {item['id']}")

        commit = item.get("commit", {})

        # 1. Git baseline
        git_result = git_baseline(commit)

        # 2. Basic LLM
        llm_result = llm_baseline(commit)

        # 3. Our system
        agent_result = agentic_system(
            item.get("agent_state", {})
        )

        results.append({
            "id": item["id"],
            "expected_intent": item.get("expected_intent"),
            "git_baseline": git_result,
            "basic_llm": llm_result,
            "agentic_system": agent_result
        })

    os.makedirs("../../evaluation/results", exist_ok=True)
    with open("../../evaluation/results/results.json", "w", encoding="utf-8") as file:
        json.dump(results, file, indent=4)

    # Calculate metrics
    from metrics import calculate_accuracy, calculate_evidence_score

    git_accuracy = calculate_accuracy(results, "git_baseline")
    llm_accuracy = calculate_accuracy(results, "basic_llm")
    agent_accuracy = calculate_accuracy(results, "agentic_system")
    evidence_score = calculate_evidence_score(results)

    print("\nEvaluation Results")
    print("----------------------")
    print(f"Git Baseline: {git_accuracy:.2f}%")
    print(f"Basic LLM: {llm_accuracy:.2f}%")
    print(f"Agentic System: {agent_accuracy:.2f}%")
    print(f"Evidence Support: {evidence_score:.2f}%")

    metrics = {
        "git_accuracy": git_accuracy,
        "llm_accuracy": llm_accuracy,
        "agent_accuracy": agent_accuracy,
        "evidence_score": evidence_score
    }

    with open("../../evaluation/results/metrics.json", "w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=4)

    print("\nEvaluation completed!")

if __name__ == "__main__":
    main()
