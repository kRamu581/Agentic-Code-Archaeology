import os
import re
import tempfile
import shutil
import stat
import base64
import subprocess
from contextlib import contextmanager
from git import Repo

MAX_COMMITS = 10_000
MAX_FILES = 10_000
MAX_REPOSITORY_BYTES = 500 * 1024 * 1024
MAX_FILE_BYTES = 50 * 1024 * 1024


@contextmanager
def temporary_repository():
    """Provide an isolated clone folder without failing on Windows file locks."""
    repo_path = tempfile.mkdtemp(prefix="code_archaeology_")
    try:
        yield repo_path
    finally:
        def make_writable(func, path, _exc_info):
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except OSError:
                pass

        try:
            shutil.rmtree(repo_path, onerror=make_writable)
        except OSError:
            # A virus scanner or Git may transiently retain a handle. The
            # unique folder is safe to clean up later without losing results.
            pass

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

def analyze_repository_data(github_url: str, *, revision=None, file=None, region=None, as_of=None, auth_token=None):
    if revision is not None:
        from backend.services.git_evidence import snapshot
        return snapshot(github_url, revision, file=file, region=region, as_of=as_of)
    # A unique temporary directory prevents concurrent requests from deleting
    # each other's clone or a user-owned `temp_repo` directory.
    with temporary_repository() as repo_path:
        # Clone repository
        # Explicitly clear inherited proxy variables. Development sandboxes can
        # set them to an unavailable loopback proxy, which prevents Git from
        # cloning public repositories.
        clone_env = {
            "HTTP_PROXY": "",
            "HTTPS_PROXY": "",
            "ALL_PROXY": "",
            "http_proxy": "",
            "https_proxy": "",
            "all_proxy": ""
        }
        if auth_token:
            encoded_credentials = base64.b64encode(
                f"x-access-token:{auth_token}".encode("utf-8")
            ).decode("ascii")
            clone_env.update({
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "http.https://github.com/.extraheader",
                "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {encoded_credentials}",
            })
        clone_environment = os.environ.copy()
        clone_environment.update(clone_env)
        try:
            clone_result = subprocess.run(
                ["git", "clone", "--", github_url, repo_path],
                capture_output=True,
                check=False,
                encoding="utf-8",
                errors="replace",
                env=clone_environment,
                timeout=120,
            )
        except subprocess.TimeoutExpired as error:
            raise TimeoutError("Repository clone timed out after 120 seconds.") from error
        if clone_result.returncode:
            raise RuntimeError(clone_result.stderr.strip() or "Git clone failed.")
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

        try:
            commits = list(repo.iter_commits(max_count=MAX_COMMITS + 1))
        except ValueError as error:
            raise ValueError("The repository has no commits yet.") from error
        if not commits:
            raise ValueError("The repository has no commits yet.")
        if len(commits) > MAX_COMMITS:
            raise ValueError(f"Repository exceeds the {MAX_COMMITS}-commit analysis limit.")
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

        scanned_bytes = 0
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [directory for directory in dirs if directory != ".git"]
            for file in files:
                if file_count >= MAX_FILES:
                    raise ValueError(f"Repository exceeds the {MAX_FILES}-file analysis limit.")
                file_count += 1
                file_path = os.path.join(root, file)
                if os.path.islink(file_path):
                    continue
                file_size = os.path.getsize(file_path)
                if file_size > MAX_FILE_BYTES:
                    raise ValueError("Repository contains a file larger than the 50 MB analysis limit.")
                scanned_bytes += file_size
                if scanned_bytes > MAX_REPOSITORY_BYTES:
                    raise ValueError("Repository exceeds the 500 MB analysis size limit.")
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
