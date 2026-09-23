"""Generate only figures supported by actual non-null results."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.dataset import read_json, write_json


def generate(output):
    output = Path(output)
    result = read_json(output / "final_results.json")
    raw = read_json(output / "raw" / result["run_id"] / "predictions.json")
    folder = output / "figures" / result["run_id"]
    folder.mkdir(parents=True, exist_ok=True)
    status = {}
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        write_json(folder / "manifest.json", {"status": "matplotlib unavailable; no figures fabricated"})
        return
    plt.rcParams.update({"font.size": 10, "figure.dpi": 150, "savefig.dpi": 300})

    def save(name, fig):
        fig.tight_layout()
        for extension in ("png", "pdf"):
            fig.savefig(folder / f"{name}.{extension}")
        plt.close(fig)
        status[name] = "generated from run " + result["run_id"]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for method, summary in result["methods"].items():
        rows = [r for r in raw if r["method"] == method and r["status"] == "ok"]
        if rows:
            ax.scatter([r["code_regions"] for r in rows], [r["total_seconds"] for r in rows], label=summary["name"], alpha=.7)
    ax.set(xlabel="Input code regions (intent region or diff hunks)", ylabel="Method execution seconds (shared extraction excluded)", title="Observed analysis time" + (" — unscored smoke run" if result["status"] == "unscored_smoke" else ""))
    if ax.collections:
        ax.legend(fontsize=8)
        save("analysis_time", fig)
    else:
        plt.close(fig)
        status["analysis_time"] = "no successful method timings"
    eligible = [m for m in result["methods"].values() if m["intent"]["accuracy"] is not None]
    if eligible:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.bar([m["name"] for m in eligible], [m["intent"]["accuracy"] for m in eligible])
        ax.set(ylim=(0, 1), ylabel="Normalized exact-match accuracy", title="Intent reconstruction")
        save("intent_accuracy", fig)
    else:
        status["intent_accuracy"] = "N/A — no scored intent results"
    eligible = [m for m in result["methods"].values() if any(m["scope"][k] is not None for k in ("precision", "recall", "f1"))]
    if eligible:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        for index, metric in enumerate(("precision", "recall", "f1")):
            for i, m in enumerate(eligible):
                if m["scope"][metric] is not None:
                    ax.bar(i + (index - 1) * .25, m["scope"][metric], width=.23, label=metric if i == 0 else None)
        ax.set_xticks(range(len(eligible)), [m["name"] for m in eligible])
        ax.set(ylim=(0, 1), ylabel="Score", title="Scope detection; undefined metrics omitted")
        ax.legend()
        save("scope_metrics", fig)
    else:
        status["scope_metrics"] = "N/A — no scored scope results"
    eligible = [m for m in result["methods"].values() if m["recovery"]["ndcg"] is not None]
    if eligible:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        for m in eligible:
            gold = m["recovery"]["ground_truth_ranking"]
            predicted = m["recovery"]["predicted_ranking"]
            ax.scatter(range(1, len(gold) + 1), [predicted.index(c) + 1 for c in gold], label=m["name"])
        ax.set(xlabel="Ground-truth rank", ylabel="Predicted rank", title="Recovery rankings")
        ax.legend()
        save("recovery_rankings", fig)
    else:
        status["recovery_rankings"] = "N/A — no measured recovery ranking"
    write_json(folder / "manifest.json", status)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "evaluation/results")
    generate(parser.parse_args().output)
