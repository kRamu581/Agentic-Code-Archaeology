import os
import shutil
import re
from git import Repo

def create_evidence_map(commit, file_histories):
    evidence = []

    # Commit evidence
    evidence.append({
        "id": "C1",
        "type": "commit",
        "reference": commit["hash"],
        "content": commit["message"]
    })

    # File evidence
    for index, file_name in enumerate(
        commit.get("changed_files", [])
    ):
        evidence.append({
            "id": f"F{index + 1}",
            "type": "file",
            "reference": file_name
        })

    # Diff evidence
    for index, diff in enumerate(
        commit.get("diff", [])
    ):
        evidence.append({
            "id": f"D{index + 1}",
            "type": "diff",
            "reference": diff.get("file"),
            "content": diff.get("diff", "")[:1000]
        })

    # History evidence
    for index, history in enumerate(file_histories):
        introducing = history.get(
            "introducing_commit",
            {}
        )
        evidence.append({
            "id": f"H{index + 1}",
            "type": "history",
            "reference": history.get("file"),
            "content": introducing.get("message")
        })

    return evidence

def analyze_repository_data(github_url: str):
    repo_path = "temp_repo"

    def remove_readonly(func, path, excinfo):
        import stat
        os.chmod(path, stat.S_IWRITE)
        func(path)

    if os.path.exists(repo_path):
        shutil.rmtree(repo_path, onerror=remove_readonly)

    try:
        # Clone repository
        Repo.clone_from(github_url, repo_path)
        repo = Repo(repo_path)

        def get_file_history(repo, file_path):
            try:
                commits = list(repo.iter_commits(paths=file_path))
                if not commits:
                    return None
                latest_commit = commits[0]
                original_commit = commits[-1]
                return {
                    "file": file_path,
                    "latest_change": {
                        "hash": latest_commit.hexsha[:7],
                        "message": latest_commit.message.strip(),
                        "date": str(latest_commit.committed_datetime)
                    },
                    "introducing_commit": {
                        "hash": original_commit.hexsha[:7],
                        "message": original_commit.message.strip(),
                        "date": str(original_commit.committed_datetime)
                    },
                    "total_changes": len(commits)
                }
            except Exception:
                return None

        def get_commit_diff(commit):
            try:
                diff_data = []
                if commit.parents:
                    parent = commit.parents[0]
                    diffs = parent.diff(commit, create_patch=True)
                    for diff in diffs:
                        file_name = diff.b_path or diff.a_path
                        patch = ""
                        if diff.diff:
                            patch = diff.diff.decode("utf-8", errors="ignore")
                        # Limit each file diff
                        patch = patch[:3000]
                        diff_data.append({
                            "file": file_name,
                            "diff": patch
                        })
                        # Analyze maximum 5 files
                        if len(diff_data) >= 5:
                            break
                return diff_data
            except Exception:
                return []

        commits = list(repo.iter_commits())
        commit_count = len(commits)
        commit_history = []

        for commit in commits[:10]:
            changed_files = []
            if commit.parents:
                parent = commit.parents[0]
                diffs = parent.diff(commit)
                for diff in diffs:
                    file_name = diff.b_path or diff.a_path
                    if file_name:
                        changed_files.append(file_name)
            else:
                changed_files = list(commit.stats.files.keys())

            commit_diff = get_commit_diff(commit)

            commit_history.append({
                "hash": commit.hexsha[:7],
                "message": commit.message.strip(),
                "author": str(commit.author),
                "date": str(commit.committed_datetime),
                "changed_files": changed_files,
                "diff": commit_diff
            })

        file_histories = []
        if commit_history:
            latest_changed_files = commit_history[0]["changed_files"]
            for file_path in latest_changed_files[:5]:
                history = get_file_history(repo, file_path)
                if history:
                    file_histories.append(history)

        file_count = 0
        todos = []

        for root, dirs, files in os.walk(repo_path):
            if ".git" in root:
                continue
            for file in files:
                file_count += 1
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_number, line in enumerate(f, start=1):
                            if re.search(r"\b(TODO|FIXME)\b", line, re.IGNORECASE):
                                todos.append({
                                    "file": file_path.replace(repo_path + os.sep, ""),
                                    "line": line_number,
                                    "content": line.strip()
                                })
                except Exception:
                    continue

        return {
            "commit_count": commit_count,
            "commit_history": commit_history,
            "file_histories": file_histories,
            "file_count": file_count,
            "todos": todos
        }

    finally:
        if os.path.exists(repo_path):
            try:
                shutil.rmtree(repo_path, onerror=remove_readonly)
            except Exception:
                pass
