"""Execute methods with label-free inputs and preserve every attempt."""
import copy
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend.evaluation.baselines import git_baseline, git_script_baseline, llm_baseline, agentic_system
from backend.services.evidence_verifier import audit, prediction_hash
from backend.services.git_evidence import git
from evaluation.dataset import TASKS, TARGETS, load_dataset, write_json
from evaluation.metrics import intent_metrics, scope_metrics, recovery_metrics, evidence_metrics

METHODS = {"git": "Git baseline", "git_script": "Git log/blame script", "llm": "Single-prompt LLM", "aicar": "Proposed AICAR"}


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def validate_prediction(task, result, pack):
    if not isinstance(result, dict):
        raise ValueError("Prediction must be a JSON object")
    if not isinstance(result.get("claims"), list) or not all(isinstance(c, dict) and isinstance(c.get("text"), str) for c in result["claims"]):
        raise ValueError("Prediction must include a list of textual claims")
    for claim in result["claims"]:
        if any(claim.get(k) is not None and not isinstance(claim[k], str) for k in ("commit", "file", "hunk", "quote", "kind")):
            raise ValueError("Claim references must be strings or null")
    if task == "intent":
        if not isinstance(result.get("intent"), str) or not result["intent"].strip():
            raise ValueError("Intent prediction must be nonempty text")
    elif task == "scope":
        if not isinstance(result.get("hunks"), dict) or set(result["hunks"]) != {h["id"] for h in pack["hunks"]}:
            raise ValueError("Scope prediction must classify every exact hunk ID")
        if any(v not in {"in-scope", "out-of-scope", "unclear"} for v in result["hunks"].values()):
            raise ValueError("Invalid scope class")
        if result.get("verdict") not in {"keep", "split", "justify"}:
            raise ValueError("Invalid scope verdict")
    else:
        score = result.get("score")
        if score is not None and (type(score) not in {int, float} or not math.isfinite(score) or not 0 <= score <= 1):
            raise ValueError("Recovery score must be null or a finite number in [0,1]")


def execute(dataset, output, *, smoke=False, live=False, tasks=TASKS):
    output = Path(output)
    started = now()
    clock = time.perf_counter()
    # No predictions, output replacement, or external calls before dataset validation.
    data = load_dataset(dataset, allow_unlabelled=smoke, tasks=tasks)
    preparation_seconds = time.perf_counter() - clock
    if live and (not os.getenv("GEMINI_API_KEY") or not os.getenv("GEMINI_MODEL")):
        raise ValueError("Live execution requires GEMINI_API_KEY and an explicit GEMINI_MODEL; no fallback permitted")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "_" + uuid.uuid4().hex[:8]
    run_path = output / "raw" / run_id
    raw = []
    adjudication_templates = []
    for task in tasks:
        for case in data["cases"][task]:
            pack = data["packs"][case["case_id"]]
            pack_digest = digest(pack)
            write_json(run_path / "evidence" / f"{case['case_id']}.json", pack)
            for method in METHODS:
                entry = {"case_id": case["case_id"], "task": task, "method": method,
                    "repository": case["repository"], "commit": case["revision"],
                    "file": case.get("file"), "region": case.get("region"),
                    "hunks": [h["id"] for h in pack["hunks"]], "evidence_sha256": pack_digest,
                    "repositories": 1, "files": pack["file_count"], "commits": pack["commit_count"],
                    "code_regions": 1 if task == "intent" else len(pack["hunks"]),
                    "start_time": None, "end_time": None, "total_seconds": None,
                    "mode": "live" if live and method in {"llm", "aicar"} else "offline"}
                if method == "llm" and not live:
                    entry.update(status="skipped", reason="Live LLM execution not enabled")
                    raw.append(entry)
                    continue
                entry["start_time"] = now()
                tick = time.perf_counter()
                try:
                    inputs = copy.deepcopy(pack)
                    if method == "aicar":
                        prediction = agentic_system.predict(task, inputs, live=live)
                    else:
                        prediction = {"git": git_baseline, "git_script": git_script_baseline, "llm": llm_baseline}[method].predict(task, inputs)
                    entry["prediction"] = prediction
                    validate_prediction(task, prediction, pack)
                    entry.update(status="ok", prediction=prediction, prediction_sha256=prediction_hash(prediction))
                except Exception as error:
                    # Do not persist provider exception strings, which can contain credentials/URLs.
                    entry.update(status="error", reason=type(error).__name__ + ": method failed; no prediction scored")
                entry["total_seconds"] = time.perf_counter() - tick
                entry["end_time"] = now()
                if entry["status"] == "ok":
                    entry["evidence_audit"] = audit(entry["prediction"], pack)
                    adjudication_templates.append({"case_id": case["case_id"], "method": method,
                        "prediction_sha256": entry["prediction_sha256"], "intent_correct": None,
                        "annotator": None, "rationale": None,
                        "claims": [{"text": c["claim"]["text"], "supported": None, "rationale": None}
                                   for c in entry["evidence_audit"]["claims"]]})
                raw.append(entry)
    summaries = summarize(data, raw, smoke, tasks)
    packages = {}
    for package in ("GitPython", "google-genai", "pytest", "matplotlib"):
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = None
    root = Path(__file__).resolve().parents[1]
    code_files = sorted([*root.glob("evaluation/*.py"), *root.glob("evaluation/runners/*.py"), *root.glob("backend/**/*.py")])
    try:
        code_revision = git(root, "rev-parse", "HEAD").strip()
    except ValueError:
        code_revision = "not a git repository"
    provenance = {"python": platform.python_version(), "platform": platform.platform(), "packages": packages,
        "git_version": git(root, "--version").strip(), "code_revision": code_revision,
        "code_sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in code_files},
        "dataset_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(dataset).glob("*.json"))},
        "model": os.getenv("GEMINI_MODEL") if live else None, "temperature": 0 if live else None,
        "evidence_as_of": data["manifest"]["as_of"]}
    result = {"schema_version": 1, "run_id": run_id, "status": "unscored_smoke" if smoke else "scored",
        "start_time": started, "end_time": now(), "total_seconds": time.perf_counter() - clock,
        "preparation_seconds": preparation_seconds, "timing_scope": "validation/extraction plus method execution; shared extraction is measured separately, report/plot generation excluded",
        "dataset": data["counts"], "targets_not_observed": TARGETS,
        "attempts": len(raw), "executed": sum(r["status"] != "skipped" for r in raw),
        "successful": sum(r["status"] == "ok" for r in raw), "errors": sum(r["status"] == "error" for r in raw),
        "skipped": sum(r["status"] == "skipped" for r in raw), "scored_cases": 0 if smoke else sum(len(data["cases"][t]) for t in tasks),
        "methods": summaries, "provenance": provenance}
    write_json(run_path / "predictions.json", raw)
    write_json(run_path / "manifest.json", result)
    write_json(run_path / "review_template.json", adjudication_templates)
    write_json(output / "processed" / f"{run_id}.json", summaries)
    return result, raw


def summarize(data, raw, smoke, tasks):
    summaries = {}
    for method, name in METHODS.items():
        rows = [r for r in raw if r["method"] == method]
        pairs = {t: [] for t in TASKS}
        task_status = {}
        for task in tasks:
            selected = [r for r in rows if r["task"] == task]
            complete = bool(selected) and all(r["status"] == "ok" for r in selected)
            task_status[task] = "unscored smoke" if smoke else ("complete" if complete else "unavailable: method skipped or failed")
            if not smoke and complete:
                mapping = {c["case_id"]: c for c in data["cases"][task]}
                pairs[task] = [(mapping[r["case_id"]], r["prediction"]) for r in selected]
                for row in selected:
                    pair = [(mapping[row["case_id"]], row["prediction"])]
                    row["metrics"] = intent_metrics(pair) if task == "intent" else scope_metrics(pair) if task == "scope" else None
        audits = [r["evidence_audit"] for r in rows if r["task"] == "intent" and r["status"] == "ok"] if pairs["intent"] else []
        summaries[method] = {"name": name, "task_status": task_status,
            "intent": intent_metrics(pairs["intent"]), "scope": scope_metrics(pairs["scope"]),
            "recovery": recovery_metrics(pairs["recovery"]), "evidence": evidence_metrics(audits),
            "analysis_seconds": (sum(r["total_seconds"] for r in rows if r["total_seconds"] is not None)
                                 if any(r["total_seconds"] is not None for r in rows) else None),
            "executed": sum(r["status"] != "skipped" for r in rows),
            "mode": next((r["mode"] for r in rows), None)}
    return summaries
