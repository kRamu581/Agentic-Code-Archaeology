"""Deterministic history/blame baseline; no semantic classifications inferred."""


def predict(task, pack):
    from backend.evaluation.baselines.git_baseline import predict as plain_git
    result = plain_git(task, pack)
    if task == "intent":
        by_sha = {c["hash"]: c for c in pack["commit_history"]}
        blame = pack["blame_commits"]
        sha = blame[0] if len(blame) == 1 else None
        result["introducing_commit"] = sha
        if sha:
            message = by_sha[sha]["message"]
            result["intent"] = message
            result["claims"] = [{"text": message, "quote": message, "kind": "quote", "commit": sha}]
    result["history_summary"] = {"commits": pack["commit_count"], "files": pack["file_count"], "region_blame": pack["blame_commits"]}
    return result
