def calculate_health_score(
    repository_summary,
    intent_analysis,
    recovery_analysis
):
    score = 100

    # Repository information
    total_commits = repository_summary.get("total_commits", 0)
    todo_count = repository_summary.get("todo_count", 0)

    # Less Git history
    if total_commits < 5:
        score -= 15

    # More unfinished TODOs
    if todo_count > 10:
        score -= 15

    # Recovery analysis
    recovery_text = str(recovery_analysis).lower()

    if "abandoned" in recovery_text:
        score -= 10

    if "incomplete" in recovery_text:
        score -= 10

    # Keep score between 0 and 100
    score = max(0, min(score, 100))
    return score

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
