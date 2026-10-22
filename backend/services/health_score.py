def calculate_health_score(
    repository_summary,
    intent_analysis,
    recovery_analysis
):
    metrics = calculate_health_metrics(repository_summary, recovery_analysis)
    score = (
        metrics["git_activity"] * 0.40
        + metrics["code_completeness"] * 0.35
        + metrics["recovery_potential"] * 0.25
    )
    return round(max(0, min(score, 100)), 2)

def calculate_health_metrics(
    repository_summary,
    recovery_analysis
):
    total_commits = repository_summary.get("total_commits", 0)
    todo_count = repository_summary.get("todo_count", 0)

    # Git Activity
    git_activity = min(total_commits * 5, 100)

    # Code Completeness
    completeness = max(0, 100 - (todo_count * 5))

    # Recovery Potential
    recovery_text = str(recovery_analysis).lower()
    recovery_potential = 50

    if "continue" in recovery_text:
        recovery_potential += 30

    if "high potential" in recovery_text:
        recovery_potential += 20

    return {
        "git_activity": min(git_activity, 100),
        "code_completeness": min(completeness, 100),
        "recovery_potential": min(recovery_potential, 100)
    }
