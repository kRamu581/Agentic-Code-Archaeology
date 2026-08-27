def git_baseline(commit):

    return {
        "prediction": commit.get(
            "message",
            "No commit message available"
        ),

        "method": "Git commit message baseline"
    }
