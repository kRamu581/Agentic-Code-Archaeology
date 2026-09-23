"""Temporary toy repositories are software test fixtures, NOT research data."""
import copy
import json
import math
import subprocess
from pathlib import Path

import pytest

from backend.agents.intent_agent import analyze_intent
from backend.agents.scope_agent import analyze_scope
from backend.agents.recovery_agent import analyze_recovery
from backend.services.git_evidence import git, snapshot, segment_diff
from backend.services.evidence_verifier import audit, verify_claim
from backend.evaluation.baselines import git_baseline, git_script_baseline, agentic_system
from evaluation.dataset import load_dataset, read_json, write_json
from evaluation.prepare_dataset import prepare
from evaluation.pipeline import execute, validate_prediction
from evaluation.reporting import publish
from evaluation.metrics import intent_metrics, scope_metrics, recovery_metrics, evidence_metrics


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "repo"
    path.mkdir()
    git(path, "init")
    git(path, "config", "user.email", "fixture@example.invalid")
    git(path, "config", "user.name", "Test fixture")
    (path / "main.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (path / "README.md").write_text("# Fixture\n", encoding="utf-8")
    git(path, "add", ".")
    git(path, "commit", "-m", "Implement addition")
    first = git(path, "rev-parse", "HEAD").strip()
    (path / "main.py").write_text("def add(a, b):\n    # TODO: validate types\n    return a + b\n", encoding="utf-8")
    git(path, "add", ".")
    git(path, "commit", "-m", "Document missing validation")
    second = git(path, "rev-parse", "HEAD").strip()
    return path, first, second


@pytest.fixture
def pack(repo):
    path, _, sha = repo
    return snapshot(path, sha, file="main.py", region=[1, 3], as_of="2030-01-01T00:00:00+00:00")


@pytest.fixture
def dataset(repo, tmp_path):
    directory = tmp_path / "dataset"
    prepare(repo[0], directory, "fixture")
    return directory


def test_extract_commits_files_and_features(pack):
    assert pack["commit_count"] == 2
    assert pack["file_count"] == 2
    assert pack["features"]["todo_count"] == 1
    assert pack["features"]["readme_nonempty"]
    assert pack["features"]["core_feature_completeness"] is None
    assert pack["features"]["runnable_entrypoint"] == "not executed"


def test_root_commit_diff_and_introduction(repo):
    pack = snapshot(repo[0], repo[1], file="main.py", region=[1, 2])
    assert "+def add" in pack["diff"]
    assert pack["hunks"]
    assert pack["file_histories"][0]["introducing_commit"]["hash"] == repo[1]
    assert pack["blame_commits"] == [repo[1]]


def test_dirty_tree_does_not_affect_snapshot(repo):
    before = snapshot(repo[0], repo[2], as_of="2030-01-01T00:00:00Z")
    (repo[0] / "main.py").write_text("uncommitted mutation")
    assert snapshot(repo[0], repo[2], as_of="2030-01-01T00:00:00Z") == before


@pytest.mark.parametrize("revision", ["HEAD", "abcdef", "--help", "0" * 40])
def test_invalid_revision_rejected(repo, revision):
    with pytest.raises(ValueError):
        snapshot(repo[0], revision)


def test_invalid_region_and_file(repo):
    with pytest.raises(ValueError):
        snapshot(repo[0], repo[2], file="main.py", region=[0, 100])
    with pytest.raises(ValueError):
        snapshot(repo[0], repo[2], file="missing.py", region=[1, 2])


def test_hunk_ids_stable_and_sensitive(pack):
    assert segment_diff(pack["diff"]) == pack["hunks"]
    changed = segment_diff(pack["diff"].replace("validate types", "validate arguments"))
    assert changed[0]["id"] != pack["hunks"][0]["id"]


def test_agents_offline_without_sdk_or_key(pack, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    intent = analyze_intent(pack["commit"], pack["file_histories"], [], evidence_pack=pack)
    assert intent["intent"] == pack["commit"]["message"]
    assert intent["introducing_commit"] is None
    scope = analyze_scope("task", [], evidence_pack=pack)
    assert set(scope["hunks"].values()) == {"unclear"}
    assert analyze_recovery({}, evidence_pack=pack)["score"] is None


def test_legacy_agent_interfaces_still_work(monkeypatch):
    monkeypatch.setenv("USE_GEMINI_ANALYSIS", "false")
    assert analyze_intent({"message": "x"}, [], [])["likely_intent"] == "x"
    assert "INSUFFICIENT_EVIDENCE" in analyze_scope("task", ["a.py"])
    assert "Local recovery assessment" in analyze_recovery({})


def test_evidence_quote_vs_inference(pack):
    quote = pack["commit"]["message"]
    claim = {"text": quote, "quote": quote, "kind": "quote", "commit": pack["revision"]}
    assert verify_claim(claim, pack)["supported"]
    assert not verify_claim({**claim, "kind": "interpretation"}, pack)["supported"]
    assert not verify_claim({**claim, "text": "unrelated conclusion"}, pack)["supported"]
    assert not verify_claim({**claim, "commit": "abc123"}, pack)["resolved"]
    assert not verify_claim({**claim, "file": "absent.py"}, pack)["resolved"]
    assert not verify_claim({**claim, "hunk": "invented"}, pack)["resolved"]


def test_hunk_citation_and_file_match(pack):
    hunk = pack["hunks"][0]
    claim = {"text": hunk["text"], "quote": hunk["text"], "kind": "quote", "commit": pack["revision"], "file": "main.py", "hunk": hunk["id"]}
    assert verify_claim(claim, pack)["supported"]
    assert not verify_claim({**claim, "file": "README.md"}, pack)["resolved"]


def test_missing_conclusion_citation_gets_no_credit(pack):
    result = audit({"intent": "unsupported inference", "claims": []}, pack)
    assert result["total_verifiable"] == 1
    assert result["supported"] == 0


def test_intent_metric_is_not_substring_match():
    case = {"accepted_intents": ["Add validation"], "introducing_commit": "a"}
    result = intent_metrics([(case, {"intent": "Do not add validation", "introducing_commit": None})])
    assert result["accuracy"] == 0
    assert intent_metrics([(case, {"intent": " ADD  VALIDATION ", "introducing_commit": "a"})])["accuracy"] == 1
    assert intent_metrics([])["accuracy"] is None


def test_scope_confusion_and_abstentions():
    case = {"gold_hunks": {"a": "out-of-scope", "b": "out-of-scope", "c": "in-scope", "d": "unclear"}, "gold_verdict": "split"}
    pred = {"hunks": {"a": "out-of-scope", "b": "unclear", "c": "out-of-scope", "d": "out-of-scope"}, "verdict": "split"}
    result = scope_metrics([(case, pred)])
    assert (result["tp"], result["fp"], result["fn"]) == (1, 1, 1)
    assert result["f1"] == .5
    assert result["decision_accuracy"] == 1
    assert result["gold_unclear_excluded"] == 1
    assert scope_metrics([])["precision"] is None


def test_ndcg_known_order_and_missing_scores():
    pairs = [({"case_id": "a", "gold_recoverability": 3, "gold_rank": 1}, {"score": .9}),
             ({"case_id": "b", "gold_recoverability": 1, "gold_rank": 2}, {"score": .1})]
    assert recovery_metrics(pairs)["ndcg"] == 1
    pairs[0][1]["score"] = 0
    expected = (1 + 7 / math.log2(3)) / (7 + 1 / math.log2(3))
    assert recovery_metrics(pairs)["ndcg"] == pytest.approx(expected)
    pairs[0][1]["score"] = None
    assert recovery_metrics(pairs)["ndcg"] is None


def test_evidence_denominator():
    assert evidence_metrics([])["rate"] is None
    assert evidence_metrics([{"supported": 1, "total_verifiable": 4}])["rate"] == .25


def test_templates_have_no_invented_labels(dataset):
    data = load_dataset(dataset, allow_unlabelled=True)
    assert data["counts"]["labelled"] == 0
    assert data["counts"]["pending"] == 5
    assert all(c["gold_intent"] is None for c in data["cases"]["intent"])
    with pytest.raises(ValueError, match="Missing ground truth"):
        load_dataset(dataset)


def test_duplicate_prepare_never_overwrites_labels(dataset, repo):
    before = (dataset / "intent_cases.json").read_bytes()
    with pytest.raises(ValueError, match="already registered"):
        prepare(repo[0], dataset, "fixture")
    assert (dataset / "intent_cases.json").read_bytes() == before


def test_tampered_diff_rejected_even_smoke(dataset):
    cases = read_json(dataset / "scope_cases.json")
    cases[0]["diff"] += "fabricated diff"
    write_json(dataset / "scope_cases.json", cases)
    with pytest.raises(ValueError, match="diff must exactly match"):
        load_dataset(dataset, allow_unlabelled=True)


def test_labelled_case_requires_provenance(dataset):
    cases = read_json(dataset / "intent_cases.json")
    cases[0]["annotation"]["status"] = "labelled"
    write_json(dataset / "intent_cases.json", cases)
    with pytest.raises(ValueError, match="human annotator"):
        load_dataset(dataset, allow_unlabelled=True)


@pytest.mark.parametrize("method", [git_baseline, git_script_baseline, agentic_system])
def test_baseline_execution(method, pack):
    for task in ("intent", "scope", "recovery"):
        result = method.predict(task, {**pack, "task": "validate types"})
        validate_prediction(task, result, pack)


def test_bad_model_output_rejected(pack):
    with pytest.raises(ValueError, match="every exact hunk"):
        validate_prediction("scope", {"hunks": {}, "claims": []}, pack)
    with pytest.raises(ValueError, match="finite number"):
        validate_prediction("recovery", {"score": float("nan"), "claims": []}, pack)
    with pytest.raises(ValueError, match="references must be strings"):
        validate_prediction("intent", {"intent": "test", "claims": [{"text": "test", "commit": []}]}, pack)


def test_smoke_pipeline_real_git_but_no_scored_metrics(dataset, tmp_path):
    output = tmp_path / "results"
    result, raw = execute(dataset, output, smoke=True)
    publish(result, raw, output)
    assert result["executed"] == 15
    assert result["skipped"] == 5
    assert result["errors"] == 0
    assert result["scored_cases"] == 0
    assert all(m["intent"]["accuracy"] is None for m in result["methods"].values())
    assert all(r["total_seconds"] >= 0 for r in raw if r["status"] == "ok")
    for cid in {r["case_id"] for r in raw}:
        assert len({r["evidence_sha256"] for r in raw if r["case_id"] == cid}) == 1
    assert (output / "final_results.csv").exists()
    assert (output / "evaluation_report.md").exists()
    assert (output / "timings.csv").exists()


def test_strict_failure_does_not_replace_results(dataset, tmp_path):
    output = tmp_path / "results"
    output.mkdir()
    previous = output / "final_results.json"
    previous.write_text('{"prior": true}')
    with pytest.raises(ValueError, match="Missing ground truth"):
        execute(dataset, output)
    assert previous.read_text() == '{"prior": true}'


def test_live_run_requires_explicit_configuration(dataset, tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Live execution requires"):
        execute(dataset, tmp_path / "out", smoke=True, live=True)


def test_labelled_intent_pipeline_fixture_only(dataset, tmp_path):
    cases = read_json(dataset / "intent_cases.json")
    for case in cases:
        pack = read_json(dataset / "evidence" / f"{case['case_id']}.json")
        case.update(gold_intent=pack["commit"]["message"], accepted_intents=[pack["commit"]["message"]],
                    introducing_commit=case["revision"], supporting_commits=[case["revision"]],
                    annotation={"status": "labelled", "annotator": "unit-test fixture only", "rationale": "Artificial expected output used solely to test the evaluator"})
    write_json(dataset / "intent_cases.json", cases)
    result, raw = execute(dataset, tmp_path / "out", tasks=("intent",))
    assert result["methods"]["git"]["intent"]["correct"] == 2
    assert result["methods"]["llm"]["intent"]["accuracy"] is None
    assert all("gold_intent" not in json.dumps(read_json(p)) for p in (tmp_path / "out" / "raw").glob("*/evidence/*.json"))


def test_prediction_errors_preserved_without_scoring(dataset, tmp_path, monkeypatch):
    monkeypatch.setattr(git_baseline, "predict", lambda task, pack: {"claims": [], "hunks": {}})
    result, raw = execute(dataset, tmp_path / "out", smoke=True, tasks=("intent",))
    failed = [r for r in raw if r["method"] == "git"]
    assert all(r["status"] == "error" and "prediction" in r for r in failed)
    assert result["errors"] >= 2
    assert result["methods"]["git"]["intent"]["accuracy"] is None


def test_labelled_scope_fixture_pipeline(dataset, tmp_path):
    cases = read_json(dataset / "scope_cases.json")
    for case in cases:
        case.update(task="Artificial task for software testing only",
                    task_source={"reference": "unit-test", "text": "Artificial test-only task"},
                    gold_hunks={key: "out-of-scope" for key in case["gold_hunks"]}, gold_verdict="split",
                    annotation={"status": "labelled", "annotator": "unit test", "rationale": "Synthetic assertion, never research data"})
    write_json(dataset / "scope_cases.json", cases)
    result, raw = execute(dataset, tmp_path / "out", tasks=("scope",))
    measured = result["methods"]["aicar"]["scope"]
    assert measured["fn"] == sum(len(c["gold_hunks"]) for c in cases)
    assert measured["recall"] == 0
    assert measured["decision_accuracy"] == 0


def test_duplicate_repository_origin_rejected(dataset):
    manifest = read_json(dataset / "repositories.json")
    entry = {**manifest["repositories"][0], "id": "duplicate"}
    manifest["repositories"].append(entry)
    write_json(dataset / "repositories.json", manifest)
    with pytest.raises(ValueError, match="Duplicate source repository"):
        load_dataset(dataset, allow_unlabelled=True)
