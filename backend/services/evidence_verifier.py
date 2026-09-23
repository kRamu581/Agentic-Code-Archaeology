"""Citation resolution is distinct from semantic entailment."""
import hashlib
import json


def prediction_hash(prediction):
    return hashlib.sha256(json.dumps(prediction, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def verify_claim(claim, pack):
    commits = {c["hash"]: c["message"] for c in pack["commit_history"]}
    sha = claim.get("commit")
    if sha not in commits:
        return {"resolved": False, "supported": False, "reason": "unknown commit"}
    file = claim.get("file")
    hunk_id = claim.get("hunk")
    # Files/hunks in this pack refer exclusively to the pinned snapshot.
    if (file or hunk_id) and sha != pack["revision"]:
        return {"resolved": False, "supported": False, "reason": "file/hunk snapshot mismatch"}
    if file and file not in pack["files"]:
        return {"resolved": False, "supported": False, "reason": "unknown file"}
    hunks = {h["id"]: h for h in pack["hunks"]}
    if hunk_id and hunk_id not in hunks:
        return {"resolved": False, "supported": False, "reason": "unknown hunk"}
    if hunk_id and file and not hunks[hunk_id]["file_header"].endswith(" b/" + file):
        return {"resolved": False, "supported": False, "reason": "hunk/file mismatch"}
    source = hunks[hunk_id]["text"] if hunk_id else commits[sha]
    quote = claim.get("quote", "")
    exact = bool(quote) and quote in source and claim.get("text") == quote
    supported = claim.get("kind") == "quote" and exact
    return {"resolved": True, "supported": supported,
            "reason": "verified exact extractive claim" if supported else "semantic support requires human review; no automatic credit"}


def audit(prediction, pack):
    claims = list(prediction.get("claims", []))
    # Never let omission of the main conclusion earn a perfect support score.
    conclusion = prediction.get("intent")
    if conclusion and not any(c.get("text") == conclusion for c in claims):
        claims.append({"text": conclusion, "kind": "interpretation"})
    if ("hunks" in prediction or "score" in prediction) and not claims:
        claims.append({"text": "Uncited classification/ranking", "kind": "interpretation"})
    checks = [{"claim": c, **verify_claim(c, pack)} for c in claims]
    return {"claims": checks, "supported": sum(c["supported"] for c in checks),
            "total_verifiable": len(checks), "unsupported": sum(not c["supported"] for c in checks)}
