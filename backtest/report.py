from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def generate_report(eval_results: dict[str, Any], output_dir: Optional[Path] = None) -> None:
    out_dir = output_dir or Path("docs")
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "eval_results.json"
    chart_path = out_dir / "eval_chart.png"

    # 1. Write eval_results.json
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(eval_results, f, indent=2)
    print(f"Wrote eval results to {json_path}")

    # 2. Render matplotlib bar chart: Baseline vs NammaTwin
    m = eval_results["metrics"]

    categories = ["Top-1 Accuracy", "Dept Routing Accuracy"]
    nammatwin_scores = [m["top1_accuracy"] * 100, m["dept_routing_accuracy"] * 100]
    baseline_scores = [m["baseline_top1_accuracy"] * 100, m["baseline_dept_accuracy"] * 100]

    x = range(len(categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    rects1 = ax.bar([i - width / 2 for i in x], baseline_scores, width, label="Category Baseline", color="#94a3b8")
    rects2 = ax.bar([i + width / 2 for i in x], nammatwin_scores, width, label="NammaTwin Agent", color="#0284c7")

    ax.set_ylabel("Accuracy (%)", fontsize=12)
    ax.set_title("NammaTwin vs. Category-Only Baseline (17 Historical Scenarios)", fontsize=13, pad=15)
    ax.set_xticks(list(x))
    ax.set_xticklabels(categories, fontsize=11)
    ax.set_ylim(0, 110)
    ax.legend(loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(
                f"{height:.1f}%",
                xy=(rect.get_x() + rect.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

    autolabel(rects1)
    autolabel(rects2)

    plt.tight_layout()
    plt.savefig(chart_path, dpi=200)
    plt.close()

    print(f"Generated chart at {chart_path}")
