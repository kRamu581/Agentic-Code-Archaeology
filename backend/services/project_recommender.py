def calculate_recovery_score(project):
    todo_completeness = max(0, 100 - project.get("todo_count", 0) * 5)
    completion = min(
        max(0, project.get("completion_level", 0)),
        todo_completeness,
    )
    activity_score = min(100, max(0, project.get("activity_score", 0)))
    recovery_potential = min(100, max(0, project.get("recovery_potential", 50)))
    return round(
        activity_score * 0.40
        + completion * 0.35
        + recovery_potential * 0.25,
        2,
    )


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
