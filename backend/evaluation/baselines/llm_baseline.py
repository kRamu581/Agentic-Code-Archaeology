"""One prompt over the same evidence; no specialized agents or verifier."""
from backend.services.llm import structured_prediction


def predict(task, pack):
    return structured_prediction(task, pack)
