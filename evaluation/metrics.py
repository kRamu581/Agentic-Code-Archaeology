"""Pure metrics. None means unmeasurable, never a fabricated zero."""
import math


def normalized(text):
    return " ".join(text.casefold().split())


def intent_metrics(pairs):
    if not pairs:
        return {"accuracy": None, "cases": 0, "correct": 0, "incorrect": 0, "introducing_commit_accuracy": None}
    correct = sum(normalized(pred.get("intent", "")) in {normalized(x) for x in case["accepted_intents"]} for case, pred in pairs)
    commits = sum(pred.get("introducing_commit") == case["introducing_commit"] for case, pred in pairs)
    return {"accuracy": correct / len(pairs), "cases": len(pairs), "correct": correct,
            "incorrect": len(pairs) - correct, "introducing_commit_accuracy": commits / len(pairs)}


def scope_metrics(pairs):
    tp = fp = fn = unclear = abstentions = correct = decisions = 0
    for case, pred in pairs:
        for hunk, gold in case["gold_hunks"].items():
            value = pred["hunks"].get(hunk, "unclear")
            abstentions += value == "unclear"
            if gold == "unclear":
                unclear += 1
                continue
            tp += gold == value == "out-of-scope"
            fp += gold == "in-scope" and value == "out-of-scope"
            fn += gold == "out-of-scope" and value != "out-of-scope"
        if case.get("gold_verdict"):
            decisions += 1
            correct += case["gold_verdict"] == pred.get("verdict")
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1,
            "gold_unclear_excluded": unclear, "predicted_unclear": abstentions,
            "decision_accuracy": correct / decisions if decisions else None, "cases": len(pairs)}


def recovery_metrics(pairs):
    if len(pairs) < 2 or any(p.get("score") is None for _, p in pairs):
        return {"ndcg": None, "repositories": len(pairs), "predicted_ranking": [],
                "ground_truth_ranking": [c["case_id"] for c, _ in sorted(pairs, key=lambda x: (x[0]["gold_rank"], x[0]["case_id"]))]}
    ordered = sorted(pairs, key=lambda x: (-x[1]["score"], x[0]["case_id"]))
    ideal = sorted(pairs, key=lambda x: (-x[0]["gold_recoverability"], x[0]["case_id"]))
    def dcg(items):
        return sum((2 ** c["gold_recoverability"] - 1) / math.log2(i + 2) for i, (c, _) in enumerate(items))
    denominator = dcg(ideal)
    return {"ndcg": dcg(ordered) / denominator if denominator else None, "repositories": len(pairs),
            "predicted_ranking": [c["case_id"] for c, _ in ordered],
            "ground_truth_ranking": [c["case_id"] for c, _ in sorted(pairs, key=lambda x: (x[0]["gold_rank"], x[0]["case_id"]))]}


def evidence_metrics(audits):
    supported = sum(a["supported"] for a in audits)
    total = sum(a["total_verifiable"] for a in audits)
    return {"supported": supported, "total_verifiable": total, "rate": supported / total if total else None}
