from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "docs" / "architecture.png"
BOX_W = 2.25
BOX_H = 0.8


def add_box(ax, x, y, label, color):
    box = FancyBboxPatch(
        (x, y),
        BOX_W,
        BOX_H,
        boxstyle="round,pad=0.08,rounding_size=0.04",
        linewidth=1.6,
        edgecolor="#111827",
        facecolor=color,
    )
    ax.add_patch(box)
    ax.text(x + BOX_W / 2, y + BOX_H / 2, label, ha="center", va="center", fontsize=9)


def add_arrow(ax, x1, y1, x2, y2):
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->", linewidth=1.8, color="#374151"),
    )


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12.0, 6.2))
    ax.set_xlim(0, 12.5)
    ax.set_ylim(0, 7)
    ax.axis("off")

    add_box(ax, 0.5, 5.0, "Scenario\nCatalog", "#dbeafe")
    add_box(ax, 3.15, 5.0, "Mission Phase\nPlanner", "#e0f2fe")
    add_box(ax, 5.8, 5.0, "Mission\nSimulator", "#ccfbf1")
    add_box(ax, 8.45, 5.0, "Fault\nInjection", "#ffedd5")

    add_box(ax, 0.85, 3.25, "UAV State\nData", "#ecfeff")
    add_box(ax, 3.5, 3.25, "Runtime Safety\nMonitor", "#dcfce7")
    add_box(ax, 6.15, 3.25, "Mission\nSupervisor", "#fef3c7")
    add_box(ax, 8.8, 3.25, "Simulation\nRunner", "#fde68a")

    add_box(ax, 1.4, 1.35, "State + Event\nCSV Logs", "#fee2e2")
    add_box(ax, 5.0, 1.35, "Scenario\nValidation", "#ede9fe")
    add_box(ax, 8.6, 1.35, "Analysis\nPlots", "#fce7f3")

    add_arrow(ax, 2.75, 5.4, 3.15, 5.4)
    add_arrow(ax, 5.4, 5.4, 5.8, 5.4)
    add_arrow(ax, 8.05, 5.4, 8.45, 5.4)
    add_arrow(ax, 6.9, 5.0, 2.0, 4.05)
    add_arrow(ax, 9.6, 5.0, 2.0, 4.05)
    add_arrow(ax, 3.1, 3.65, 3.5, 3.65)
    add_arrow(ax, 5.75, 3.65, 6.15, 3.65)
    add_arrow(ax, 8.4, 3.65, 8.8, 3.65)
    add_arrow(ax, 9.9, 3.25, 2.5, 2.15)
    add_arrow(ax, 9.9, 3.25, 6.1, 2.15)
    add_arrow(ax, 9.9, 3.25, 9.7, 2.15)

    ax.text(
        6.25,
        6.45,
        "Simulation-Based Runtime Safety Monitoring for Autonomous UAV Missions",
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
