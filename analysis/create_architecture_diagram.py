from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "docs" / "architecture.png"


def add_box(ax, x, y, label, color):
    box = FancyBboxPatch(
        (x, y),
        3.0,
        0.8,
        boxstyle="round,pad=0.08,rounding_size=0.04",
        linewidth=1.6,
        edgecolor="#111827",
        facecolor=color,
    )
    ax.add_patch(box)
    ax.text(x + 1.5, y + 0.4, label, ha="center", va="center", fontsize=10)


def add_arrow(ax, x1, y1, x2, y2):
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->", linewidth=1.8, color="#374151"),
    )


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 6)
    ax.axis("off")

    add_box(ax, 0.6, 4.4, "Mission\nSimulator", "#dbeafe")
    add_box(ax, 4.9, 4.4, "UAV State\nData", "#e0f2fe")
    add_box(ax, 2.75, 2.75, "Runtime Safety\nMonitor", "#dcfce7")
    add_box(ax, 0.6, 1.1, "Safety Status +\nRecommended Action", "#fef3c7")
    add_box(ax, 4.9, 1.1, "CSV Logs +\nAnalysis Plots", "#fee2e2")

    add_arrow(ax, 3.65, 4.8, 4.9, 4.8)
    add_arrow(ax, 6.4, 4.4, 4.25, 3.55)
    add_arrow(ax, 2.75, 3.15, 2.1, 1.9)
    add_arrow(ax, 3.75, 2.75, 5.2, 1.9)

    ax.text(
        4.5,
        5.55,
        "Runtime Safety Monitoring for Autonomous UAV Missions",
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=170)
    plt.close(fig)
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()

