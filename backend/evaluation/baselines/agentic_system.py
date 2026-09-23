"""Evaluate the existing agents with a reproducible evidence audit."""
from backend.agents.intent_agent import analyze_intent
from backend.agents.scope_agent import analyze_scope
from backend.agents.recovery_agent import analyze_recovery
from backend.services.evidence_verifier import audit


def predict(task, pack, live=False):
    kwargs = {"evidence_pack": pack, "live": live}
    if task == "intent":
        result = analyze_intent(pack["commit"], pack["file_histories"], pack["hunks"], **kwargs)
    elif task == "scope":
        result = analyze_scope(pack["task"], pack["commit"]["changed_files"], **kwargs)
    else:
        result = analyze_recovery(pack["features"], **kwargs)
    result["evidence_audit"] = audit(result, pack)
    return result
