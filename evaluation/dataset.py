"""Dataset preparation and strict, evidence-grounded validation."""
import json
import math
import re
from pathlib import Path

from backend.services.git_evidence import git, resolve
from backend.services.repository_analyzer import analyze_repository_data

TASKS = ("intent", "scope", "recovery")
TARGETS = {"repositories": 25, "intent": 40, "scope": 30, "recovery": 20, "commits_approximate": 1800}


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def load_dataset(directory, allow_unlabelled=False, tasks=TASKS):
    directory = Path(directory).resolve()
    manifest = read_json(directory / "repositories.json")
    require(isinstance(manifest, dict) and manifest.get("schema_version") == 1, "Unsupported dataset schema")
    repos = manifest["repositories"]
    require(isinstance(repos, list) and bool(repos), "No source repositories registered")
    repo_map = {}
    unique_sources = set()
    origins = set()
    for repo in repos:
        require(nonempty(repo.get("id")) and repo["id"] not in repo_map, "Duplicate/missing repository ID")
        path = (directory / repo["path"]).resolve()
        require(path not in unique_sources, "Duplicate source repository path")
        unique_sources.add(path)
        resolve(path, repo["revision"])
        require(nonempty(repo.get("source")), "Repository source/provenance required")
        origin = repo["source"].rstrip("/").removesuffix(".git")
        require(origin not in origins, "Duplicate repository source/origin")
        origins.add(origin)
        repo_map[repo["id"]] = {**repo, "resolved_path": str(path)}
    cases = {task: read_json(directory / f"{task}_cases.json") for task in TASKS}
    packs, ids, cache = {}, set(), {}
    pending = []
    for task in TASKS:
        require(isinstance(cases[task], list), f"{task}: cases must be a JSON list")
        for case in cases[task]:
            cid = case.get("case_id")
            require(isinstance(cid, str) and re.fullmatch(r"[A-Za-z0-9_-]+", cid) and cid not in ids, "Invalid/duplicate case ID")
            ids.add(cid)
            require(case.get("repository") in repo_map, f"{cid}: unknown repository")
            repo = repo_map[case["repository"]]
            rev = resolve(repo["resolved_path"], case.get("revision"))
            reachable = git(repo["resolved_path"], "rev-list", repo["revision"]).splitlines()
            require(rev in reachable, f"{cid}: revision outside pinned repository history")
            if task == "intent":
                require(nonempty(case.get("file")) and isinstance(case.get("region"), list) and len(case["region"]) == 2,
                        f"{cid}: file and [start,end] region required")
            key = (repo["id"], rev, case.get("file") if task == "intent" else None, tuple(case.get("region", [])) if task == "intent" else ())
            if key not in cache:
                cache[key] = analyze_repository_data(repo["resolved_path"], revision=rev,
                    file=case.get("file") if task == "intent" else None,
                    region=case.get("region") if task == "intent" else None, as_of=manifest["as_of"])
            pack = {**cache[key], "repository": repo["id"], "source_repository": repo["source"]}
            if task == "scope":
                require(case.get("diff") == pack["diff"], f"{cid}: diff must exactly match pinned commit")
                require(set(case.get("gold_hunks", {})) == {h["id"] for h in pack["hunks"]}, f"{cid}: gold hunk IDs differ from Git")
                require(bool(pack["hunks"]), f"{cid}: no text hunks to classify")
                pack["task"] = case.get("task")
            packs[cid] = pack
            annotation = case.get("annotation", {})
            require(annotation.get("status") in {"pending", "labelled"}, f"{cid}: annotation status must be pending or labelled")
            if annotation["status"] != "labelled":
                pending.append(cid)
                continue
            require(nonempty(annotation.get("annotator")) and nonempty(annotation.get("rationale")), f"{cid}: human annotator and evidence rationale required")
            if task == "intent":
                require(nonempty(case.get("gold_intent")), f"{cid}: gold_intent required")
                require(isinstance(case.get("accepted_intents"), list) and bool(case["accepted_intents"]) and all(nonempty(x) for x in case["accepted_intents"]), f"{cid}: accepted_intents required")
                require(case["gold_intent"] in case["accepted_intents"], f"{cid}: gold_intent must be accepted")
                supporting = case.get("supporting_commits")
                require(isinstance(supporting, list) and bool(supporting), f"{cid}: supporting commits required")
                for sha in [case.get("introducing_commit"), *supporting]:
                    resolve(repo["resolved_path"], sha)
                    require(sha in reachable and sha in {c["hash"] for c in pack["commit_history"]}, f"{cid}: evidence is after case snapshot")
                require(case["introducing_commit"] in supporting, f"{cid}: include introducing commit in supporting_commits")
            elif task == "scope":
                require(nonempty(case.get("task")), f"{cid}: actual task text required")
                source = case.get("task_source", {})
                require(nonempty(source.get("reference")) and nonempty(source.get("text")), f"{cid}: task source reference and archived quotation required")
                require(all(v in {"in-scope", "out-of-scope", "unclear"} for v in case["gold_hunks"].values()), f"{cid}: label every hunk")
                require(case.get("gold_verdict") in {None, "keep", "split", "justify"}, f"{cid}: invalid verdict")
            else:
                grade = case.get("gold_recoverability")
                require(type(grade) is int and 0 <= grade <= 3, f"{cid}: recoverability grade must be integer 0..3")
                require(type(case.get("gold_rank")) is int and case["gold_rank"] > 0, f"{cid}: positive gold_rank required")
                require(case.get("unfinished") is True, f"{cid}: human confirmation that repository is unfinished required")
    recovery = [c for c in cases["recovery"] if c["annotation"]["status"] == "labelled"]
    require(len({c["repository"] for c in recovery}) == len(recovery), "Recovery cohort must contain distinct repositories")
    for a in recovery:
        for b in recovery:
            require(not (a["gold_rank"] < b["gold_rank"] and a["gold_recoverability"] < b["gold_recoverability"]), "Recovery ranks contradict relevance grades")
    if not allow_unlabelled:
        for task in tasks:
            require(bool(cases[task]), f"Missing ground truth: no {task} cases. See evaluation/ANNOTATION_GUIDE.md")
            missing = [c["case_id"] for c in cases[task] if c["annotation"]["status"] != "labelled"]
            require(not missing, f"Missing ground truth: {task}: {', '.join(missing)}. Complete annotation or use --smoke (unscored).")
        if "recovery" in tasks:
            require(len(recovery) >= 2, "Recovery nDCG requires at least two distinct labelled repositories")
    counts = {task: len(cases[task]) for task in TASKS}
    counts.update({"repositories": len(repos), "commits": sum(len(git(r["resolved_path"], "rev-list", r["revision"]).splitlines()) for r in repo_map.values()),
                   "labelled": sum(c["annotation"]["status"] == "labelled" for rows in cases.values() for c in rows), "pending": len(pending)})
    return {"manifest": manifest, "repositories": repo_map, "cases": cases, "packs": packs, "counts": counts}
