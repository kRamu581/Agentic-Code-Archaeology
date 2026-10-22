def build_repository_graph(commit_history):
    nodes = []
    edges = []

    file_nodes = set()

    for commit in commit_history:

        commit_id = f"commit-{commit['hash']}"

        nodes.append({
            "id": commit_id,
            "label": commit["hash"],
            "message": commit.get("message", ""),
            "type": "commit"
        })

        for file_name in commit.get("changed_files", []):
            file_id = f"file-{file_name}"

            if file_id not in file_nodes:
                nodes.append({
                    "id": file_id,
                    "label": file_name,
                    "type": "file"
                })
                file_nodes.add(file_id)

            edges.append({
                "source": commit_id,
                "target": file_id
            })

    return {
        "nodes": nodes,
        "edges": edges
    }
