"""Tables and figures are derived exclusively from saved run outputs."""
import csv
import json
import shutil
from pathlib import Path

from evaluation.dataset import write_json

NA = "N/A — insufficient ground truth"


def value(number):
    return f"{number:.4f}" if number is not None else NA


def table(result):
    rows = ["Method | Intent Accuracy | Evidence Support | Scope F1 | Recovery nDCG",
            "--- | --- | --- | --- | ---"]
    for item in result["methods"].values():
        rows.append(" | ".join([item["name"], value(item["intent"]["accuracy"]), value(item["evidence"]["rate"]),
                                value(item["scope"]["f1"]), value(item["recovery"]["ndcg"])]))
    return "\n".join(rows)


def save_csv(path, rows, fields):
    with Path(path).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def publish(result, raw, output, report_path=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    existing = output / "final_results.json"
    if existing.exists():
        previous = json.loads(existing.read_text(encoding="utf-8"))
        if not isinstance(previous, dict) or previous.get("schema_version") != 1:
            archive = output / "legacy_unverified" / "final_results.json"
            archive.parent.mkdir(exist_ok=True)
            if not archive.exists():
                shutil.copy2(existing, archive)
    write_json(existing, result)
    rows = [{"Method": m["name"], "Intent Accuracy": value(m["intent"]["accuracy"]),
             "Evidence Support": value(m["evidence"]["rate"]), "Scope F1": value(m["scope"]["f1"]),
             "Recovery nDCG": value(m["recovery"]["ndcg"])} for m in result["methods"].values()]
    save_csv(output / "final_results.csv", rows, list(rows[0]))
    fields = ["method", "task", "case_id", "status", "mode", "start_time", "end_time", "total_seconds", "repositories", "files", "commits", "code_regions", "evidence_sha256"]
    save_csv(output / "raw" / result["run_id"] / "timings.csv", raw, fields)
    # Latest timing file is a convenience copy; immutable run data remains available.
    save_csv(output / "timings.csv", raw, fields)
    counts = result["dataset"]
    sections = [
        ("Experimental setup", f"Run `{result['run_id']}`: **{result['status']}**. Pinned Git objects; shared evidence per case. Python {result['provenance']['python']}. Model: {result['provenance']['model'] or 'disabled'}. All measurements below come from this run."),
        ("Dataset size", json.dumps(counts, indent=2)),
        ("Dataset composition", "Source paths, origins and immutable revisions: evaluation/datasets/repositories.json. Code-case candidates are commits changing source; recovery eligibility is unconfirmed until annotated. Targets (25 repositories, 40 intent, 30 scope, 20 recovery, approximately 1,800 commits) are not achieved dataset counts."),
        ("Ground-truth methodology", "Human annotation is mandatory; see evaluation/ANNOTATION_GUIDE.md. No labels are copied from the paper, legacy examples, commit messages, or model predictions. Intent uses preregistered normalized exact accepted answers; this is a strict textual metric, not a semantic correctness claim. Human semantic review is exported separately and not automatically scored."),
        ("Baselines", "Git: commit message extraction; scope abstention; no recovery rank. Git log/blame script: single-origin line-blame message plus history summary; ambiguous provenance abstains. Single-prompt Gemini: one common evidence pack per task, no specialized agent or verifier. Offline runs skip Gemini. No manual human analysis time is claimed."),
        ("AICAR architecture", "Existing repository analyzer's pinned-snapshot path, existing intent/scope/recovery agents with structured evaluation outputs, and evidence verifier. Dashboard's LangGraph/report route is not timed. Offline AICAR retains intent message fallback and abstains on semantic scope/recovery. Live outputs use specialized task instructions. This is a task-agent evaluation, not a measured end-to-end dashboard benchmark."),
        ("Intent results", "\n".join(f"{m['name']}: {m['intent']}" for m in result["methods"].values())),
        ("Evidence-support results", "\n".join(f"{m['name']}: {m['evidence']}" for m in result["methods"].values()) + "\nOnly exact extractive claims receive automatic support credit. Resolvable citations alone do not prove semantic support. Interpretations are flagged for human review; this conservative measure is not a semantic entailment score. Smoke audits are retained but not promoted to research metrics."),
        ("Scope precision/recall/F1", "\n".join(f"{m['name']}: {m['scope']}" for m in result["methods"].values()) + "\nOut-of-scope is the positive class. Gold unclear hunks are excluded from binary metrics and counted separately. Predicted unclear on a positive is a false negative. Zero denominators yield null, not invented scores."),
        ("Recovery nDCG", "\n".join(f"{m['name']}: {m['recovery']}" for m in result["methods"].values()) + "\nFull-cohort nDCG uses gain 2^grade-1 and log2(position+1) discounts, grades 0..3; deterministic case-ID tie break. At least two distinct human-labelled repositories are required. Any missing score makes the cohort metric unavailable."),
        ("Analysis time", f"Measured pipeline seconds: {result['total_seconds']:.6f}; shared validation/extraction: {result['preparation_seconds']:.6f}. Executed: {result['executed']}; successful: {result['successful']}; errors: {result['errors']}; skipped: {result['skipped']}. See timings.csv for timestamps and actual input counts. {result['timing_scope']}. No scaling trend or speedup is inferred from a single smoke run."),
        ("Comparison table", table(result)),
        ("Limitations", "N/A in an unlabelled run means insufficient ground truth. In scored runs, consult task_status for missing methods or failures; recovery abstention and zero-denominator metrics also remain unavailable. No live model result exists in offline mode. One self-repository is not a representative benchmark; candidate regions need human selection. Entry points, dependencies, deployment and feature completeness are not executed/verified. Large/binary blobs are excluded from text feature counts and listed in evidence. Merge diffs use the first parent. No dashboard or provider integration success is implied. Legacy results and paper claims are excluded; paper files are unchanged."),
        ("Reproducibility instructions", "From repository root: `python -m pytest -q` then `python evaluation/runners/run_all.py --smoke`. After human annotation: `python evaluation/runners/run_all.py` for offline methods; add `--live` with GEMINI_API_KEY and GEMINI_MODEL set for live comparison. Run `python evaluation/figures.py` to regenerate figures. Immutable raw manifests contain code/dataset hashes, environment versions and complete input packs. Timing and live provider responses may vary."),
    ]
    content = "# AICAR reproducible evaluation\n\n" + "\n\n".join(f"## {heading}\n\n{text}" for heading, text in sections) + "\n"
    report_path = Path(report_path) if report_path else output / "evaluation_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content, encoding="utf-8")
    (output / "raw" / result["run_id"] / "evaluation_report.md").write_text(content, encoding="utf-8")
