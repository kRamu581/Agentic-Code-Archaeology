def calculate_recovery_score(project):
    score = 0

    # Higher completion is better
    completion = project.get("completion_level", 0)
    score += completion * 0.5

    # Fewer TODOs is better
    todo_count = project.get("todo_count", 0)
    todo_score = max(0, 20 - todo_count)
    score += todo_score

    # Recent activity
    activity_score = project.get("activity_score", 0)
    score += activity_score * 0.3

    return round(min(score, 100), 2)


def rank_projects(projects):
    ranked_projects = []

    for project in projects:
        recovery_score = calculate_recovery_score(project)

        ranked_projects.append({
            **project,
            "recovery_score": recovery_score
        })

    return sorted(
        ranked_projects,
        key=lambda project: project["recovery_score"],
        reverse=True
    )
