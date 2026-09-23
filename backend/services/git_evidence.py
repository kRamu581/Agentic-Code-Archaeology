"""Read immutable Git objects, never the (possibly dirty) working tree."""
import hashlib
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def git(path, *args):
    result = subprocess.run(
        ["git", "-c", "core.quotepath=false", "-C", str(path), *args],
        capture_output=True, check=False, encoding="utf-8", errors="replace",
        timeout=120,
    )
    if result.returncode:
        raise ValueError(f"Git extraction failed ({args[0]}): {result.stderr.strip()}")
    return result.stdout


def resolve(path, revision):
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Repository revisions must be full 40-character commit hashes")
    return git(path, "rev-parse", "--verify", revision + "^{commit}").strip()


def segment_diff(patch):
    """Stable IDs include file headers, hunk offsets and content (not ordinal only)."""
    hunks = []
    file_header = ""
    current = None
    for line in patch.splitlines(keepends=True):
        if line.startswith("diff --git "):
            file_header = line.rstrip("\n")
            current = None
        elif line.startswith("@@ "):
            current = {"file_header": file_header, "header": line.rstrip("\n"), "text": line}
            hunks.append(current)
        elif current is not None:
            current["text"] += line
    for hunk in hunks:
        digest = hashlib.sha256((hunk["file_header"] + "\n" + hunk["text"]).encode()).hexdigest()
        hunk["id"] = "hunk_" + digest[:20]
    return hunks


def snapshot(path, revision, file=None, region=None, as_of=None):
    revision = resolve(path, revision)
    files = git(path, "ls-tree", "-r", "--name-only", revision).splitlines()
    history = []
    for sha in git(path, "rev-list", revision).splitlines():
        history.append({"hash": sha, "message": git(path, "show", "-s", "--format=%B", sha).strip()})
    patch = git(path, "show", "--format=", "--root", "--first-parent", "--no-ext-diff", "--no-renames", "--unified=3", revision, "--")
    changed = git(path, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "--first-parent", revision).splitlines()
    commit = {"hash": revision, "message": history[0]["message"], "changed_files": changed,
              "diff": [{"file": "(complete commit patch)", "diff": patch}]}
    histories = []
    blame = []
    source = None
    if file:
        if file not in files:
            raise ValueError(f"File does not exist at pinned revision: {file}")
        source = git(path, "show", f"{revision}:{file}")
        revisions = git(path, "log", "--format=%H", revision, "--", file).splitlines()
        histories = [{"file": file, "introducing_commit": {"hash": revisions[-1]}, "total_changes": len(revisions)}]
        if region:
            start, end = region
            if not (isinstance(start, int) and isinstance(end, int) and 1 <= start <= end <= len(source.splitlines())):
                raise ValueError("Region must identify existing 1-based inclusive lines")
            source = "\n".join(source.splitlines()[start - 1:end])
            raw = git(path, "blame", "--line-porcelain", "-L", f"{start},{end}", revision, "--", file)
            blame = list(dict.fromkeys(re.findall(r"^([0-9a-f]{40}) \d+ \d+", raw, re.M)))
    # Only tracked text files. Large/binary blobs are explicitly excluded from counts.
    texts, excluded = {}, []
    for name in files:
        size = int(git(path, "cat-file", "-s", f"{revision}:{name}"))
        if size > 200_000:
            excluded.append(name)
            continue
        content = git(path, "show", f"{revision}:{name}")
        if "\x00" in content:
            excluded.append(name)
        else:
            texts[name] = content
    readmes = [n for n in texts if Path(n).name.lower().startswith("readme")]
    observed = datetime.fromisoformat(as_of.replace("Z", "+00:00")) if as_of else datetime.now(timezone.utc)
    if observed.tzinfo is None:
        raise ValueError("as_of must include a timezone")
    committed = datetime.fromisoformat(git(path, "show", "-s", "--format=%cI", revision).strip())
    features = {
        "commit_count": len(history), "file_count": len(files),
        "last_commit_age_days": (observed - committed).total_seconds() / 86400,
        "readme_files": readmes, "readme_nonempty": any(texts[n].strip() for n in readmes),
        "test_files": [n for n in files if re.search(r"(^|/)(tests?/|test_|.*[._]test\.)", n)],
        "todo_count": sum(len(re.findall(r"\b(?:TODO|FIXME)\b", t)) for t in texts.values()),
        "entrypoint_candidates": [n for n in files if Path(n).name in {"main.py", "app.py", "package.json", "manage.py"}],
        "documentation_files": [n for n in files if n.lower().endswith((".md", ".rst"))],
        "dependency_manifests": [n for n in files if Path(n).name in {"requirements.txt", "pyproject.toml", "package.json", "Cargo.toml", "go.mod"}],
        "deployment_files": [n for n in files if Path(n).name in {"Dockerfile", "docker-compose.yml", "vercel.json"} or n.startswith(".github/workflows/")],
        "core_feature_completeness": None, "dependency_status": "not executed",
        "deployment_status": "not verified", "runnable_entrypoint": "not executed",
        "readme_completeness": "requires human assessment", "excluded_text_files": excluded,
    }
    return {"revision": revision, "as_of": observed.isoformat(), "commit": commit,
            "commit_history": history, "file_histories": histories, "files": files,
            "file": file, "region": region, "source": source, "blame_commits": blame,
            "diff": patch, "hunks": segment_diff(patch), "features": features,
            "commit_count": len(history), "file_count": len(files), "todos": []}
