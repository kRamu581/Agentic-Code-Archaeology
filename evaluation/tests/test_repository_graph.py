import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from services.repository_graph import build_repository_graph


def test_repository_graph_keeps_shared_file_connected_and_includes_commit_message():
    graph = build_repository_graph([
        {"hash": "abc1234", "message": "Add feature", "changed_files": ["src/main.py"]},
        {"hash": "def5678", "message": "Fix feature", "changed_files": ["src/main.py"]},
    ])

    file_nodes = [node for node in graph["nodes"] if node["type"] == "file"]
    commit_nodes = [node for node in graph["nodes"] if node["type"] == "commit"]
    assert len(file_nodes) == 1
    assert [node["message"] for node in commit_nodes] == ["Add feature", "Fix feature"]
    assert {edge["target"] for edge in graph["edges"]} == {file_nodes[0]["id"]}
    assert len(graph["edges"]) == 2
