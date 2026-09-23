"""Regenerate figures only from the latest measured run."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from evaluation.figures import generate

if __name__ == "__main__":
    generate(ROOT / "evaluation/results")
