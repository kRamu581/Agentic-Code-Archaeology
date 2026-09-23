def predict(task, pack):
    commit = pack["commit"]
    if task == "intent":
        message = commit["message"]
        return {"intent": message, "introducing_commit": None, "confidence": "LOW",
                "claims": [{"text": message, "quote": message, "kind": "quote", "commit": commit["hash"]}]}
    if task == "scope":
        return {"hunks": {h["id"]: "unclear" for h in pack["hunks"]}, "verdict": "justify", "confidence": "LOW", "claims": []}
    return {"score": None, "confidence": "LOW", "claims": [], "reason": "Git does not supply recoverability scores"}


def git_baseline(commit):

    return {
        "prediction": commit.get(
            "message",
            "No commit message available"
        ),

        "method": "Git commit message baseline"
    }
