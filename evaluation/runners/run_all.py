"""Strict by default: incomplete annotation fails before any methods run."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from evaluation.dataset import TASKS
from evaluation.pipeline import execute
from evaluation.reporting import publish, table


def main(default_tasks=TASKS):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "evaluation/datasets")
    parser.add_argument("--output", type=Path, default=ROOT / "evaluation/results")
    parser.add_argument("--smoke", action="store_true", help="Run real evidence with no ground-truth scoring")
    parser.add_argument("--live", action="store_true", help="Enable Gemini explicitly; requires model and key")
    parser.add_argument("--no-figures", action="store_true")
    args = parser.parse_args()
    try:
        result, raw = execute(args.dataset, args.output, smoke=args.smoke, live=args.live, tasks=default_tasks)
        report = ROOT / "evaluation/reports/evaluation_report.md" if args.output.resolve() == ROOT / "evaluation/results" else None
        publish(result, raw, args.output, report)
        if not args.no_figures:
            from evaluation.figures import generate
            generate(args.output)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f"Evaluation stopped: {error}\n")
    print(table(result))
    print(f"Run {result['run_id']}: {result['executed']} executed, {result['errors']} errors, {result['skipped']} skipped; {result['total_seconds']:.6f}s")
    return 3 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
