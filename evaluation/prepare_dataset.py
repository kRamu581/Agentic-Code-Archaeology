"""Add a real local checkout to the dataset; never create semantic labels."""
import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.services.git_evidence import git, snapshot
from evaluation.dataset import TASKS, read_json, write_json


def prepare(repository, directory, repo_id, limit=4):
    directory = Path(directory).resolve()
    repository = Path(repository).resolve()
    revision = git(repository, "rev-parse", "HEAD").strip()
    manifest_path = directory / "repositories.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else {
        "schema_version": 1, "as_of": datetime.now(timezone.utc).isoformat(), "repositories": []}
    if any(r["id"] == repo_id or (directory / r["path"]).resolve() == repository for r in manifest["repositories"]):
        raise ValueError("Repository already registered; existing annotations are never overwritten")
    try:
        source = git(repository, "remote", "get-url", "origin").strip()
    except ValueError:
        source = str(repository)
    manifest["repositories"].append({"id": repo_id, "source": source,
        "path": Path(os.path.relpath(repository, directory)).as_posix(), "revision": revision})
    cases = {t: read_json(directory / f"{t}_cases.json") if (directory / f"{t}_cases.json").exists() else [] for t in TASKS}
    pending = {"status": "pending", "annotator": None, "rationale": None}
    # Include only commits changing source code. Documentation commits are not invented code cases.
    selected = 0
    for sha in git(repository, "rev-list", revision).splitlines():
        changed = git(repository, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "--first-parent", sha).splitlines()
        files = set(git(repository, "ls-tree", "-r", "--name-only", sha).splitlines())
        source_files = [f for f in changed if f in files and Path(f).name != "__init__.py" and Path(f).suffix in {".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".go", ".rs", ".c", ".cpp"}]
        if not source_files:
            continue
        selected += 1
        file = sorted(source_files)[0]
        lines = len(git(repository, "show", f"{sha}:{file}").splitlines())
        if not lines:
            continue
        common = {"repository": repo_id, "revision": sha, "annotation": pending.copy()}
        cid = f"{repo_id}_intent_{sha[:12]}"
        case = {**common, "case_id": cid, "file": file, "region": [1, min(lines, 30)],
                "gold_intent": None, "accepted_intents": [], "introducing_commit": None, "supporting_commits": []}
        cases["intent"].append(case)
        pack = snapshot(repository, sha, file=file, region=case["region"], as_of=manifest["as_of"])
        write_json(directory / "evidence" / f"{cid}.json", pack)
        cid = f"{repo_id}_scope_{sha[:12]}"
        if pack["hunks"]:
            cases["scope"].append({**common, "case_id": cid, "task": None,
                "task_source": {"reference": None, "text": None}, "diff": pack["diff"],
                "gold_hunks": {h["id"]: None for h in pack["hunks"]}, "gold_verdict": None})
            write_json(directory / "evidence" / f"{cid}.json", pack)
        if selected >= limit:
            break
    cid = f"{repo_id}_recovery"
    cases["recovery"].append({"case_id": cid, "repository": repo_id, "revision": revision,
        "unfinished": None, "gold_rank": None, "gold_recoverability": None, "annotation": pending.copy()})
    write_json(directory / "evidence" / f"{cid}.json", snapshot(repository, revision, as_of=manifest["as_of"]))
    for task in TASKS:
        write_json(directory / f"{task}_cases.json", cases[task])
    write_json(manifest_path, manifest)
    return {t: len(cases[t]) for t in TASKS}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=ROOT)
    parser.add_argument("--dataset", type=Path, default=ROOT / "evaluation/datasets")
    parser.add_argument("--id", default="aicar")
    parser.add_argument("--limit", type=int, default=4)
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be positive")
    try:
        print(prepare(args.repository, args.dataset, args.id, args.limit))
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()
