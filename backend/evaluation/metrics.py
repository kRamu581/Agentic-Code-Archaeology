def calculate_accuracy(results, method):
    correct = 0
    total = len(results)

    for item in results:
        expected = item.get("expected_intent", "").lower().strip()

        prediction = item.get(method, {}).get("prediction", "")

        # If prediction is JSON/dict
        if isinstance(prediction, dict):
            prediction = prediction.get("likely_intent", "")
        elif isinstance(prediction, str) and prediction.startswith("{"):
            import json
            try:
                prediction = json.loads(prediction).get("likely_intent", "")
            except Exception:
                pass

        prediction = str(prediction).lower()

        # Simple keyword matching for MVP
        if expected and expected in prediction:
            correct += 1

    if total == 0:
        return 0

    return (correct / total) * 100

def calculate_evidence_score(results):
    supported = 0
    total = len(results)

    for item in results:
        prediction = item.get("agentic_system", {}).get("prediction", {})

        if isinstance(prediction, str) and prediction.startswith("{"):
            import json
            try:
                prediction = json.loads(prediction)
            except Exception:
                pass

        if isinstance(prediction, dict):
            evidence = prediction.get("evidence", [])
            if len(evidence) > 0:
                supported += 1

    if total == 0:
        return 0

    return (supported / total) * 100

def calculate_scope_metrics(tp, fp, fn):
    precision = (
        tp / (tp + fp)
        if (tp + fp) > 0
        else 0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else 0
    )

    f1 = (
        2 * precision * recall /
        (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1
    }
