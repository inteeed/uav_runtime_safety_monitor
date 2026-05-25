import argparse
import csv
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "safety_limits.json"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"


def read_log(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_limits(path: Path) -> Dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def values(rows: Iterable[Dict[str, str]], key: str) -> List[float]:
    return [float(row[key]) for row in rows]


def rows_by_severity(
    rows: Iterable[Dict[str, str]], severity: str
) -> List[Dict[str, str]]:
    return [row for row in rows if row.get("severity") == severity]


def plot_trajectory(
    rows: List[Dict[str, str]], limits: Dict[str, object], output_path: Path
) -> None:
    geofence = limits["geofence"]
    x_min = float(geofence["x_min_m"])
    x_max = float(geofence["x_max_m"])
    y_min = float(geofence["y_min_m"])
    y_max = float(geofence["y_max_m"])

    x = values(rows, "x_m")
    y = values(rows, "y_m")
    warnings = rows_by_severity(rows, "WARNING")
    critical = rows_by_severity(rows, "CRITICAL")

    fig, ax = plt.subplots(figsize=(7.5, 6.0))
    ax.add_patch(
        Rectangle(
            (x_min, y_min),
            x_max - x_min,
            y_max - y_min,
            fill=False,
            linewidth=2.0,
            edgecolor="#2f855a",
            label="Geofence",
        )
    )
    ax.plot(x, y, color="#2563eb", linewidth=2.0, label="UAV trajectory")
    ax.scatter([0.0], [0.0], marker="s", color="#111827", s=60, label="Home")
    ax.scatter([x[0]], [y[0]], marker="o", color="#0f766e", s=50, label="Start")
    ax.scatter([x[-1]], [y[-1]], marker="D", color="#4b5563", s=50, label="End")

    if warnings:
        ax.scatter(
            values(warnings, "x_m"),
            values(warnings, "y_m"),
            marker="^",
            color="#f59e0b",
            s=70,
            linewidth=1.5,
            label="Warning",
        )

    if critical:
        ax.scatter(
            values(critical, "x_m"),
            values(critical, "y_m"),
            marker="x",
            color="#dc2626",
            s=90,
            linewidth=2.0,
            label="Critical event",
        )

    ax.set_title("UAV Mission Trajectory with Geofence")
    ax.set_xlabel("x position [m]")
    ax.set_ylabel("y position [m]")
    ax.axis("equal")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def plot_altitude(
    rows: List[Dict[str, str]], limits: Dict[str, object], output_path: Path
) -> None:
    time_s = values(rows, "time_s")
    altitude = values(rows, "z_m")
    max_altitude = float(limits["max_altitude_m"])

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.plot(time_s, altitude, color="#2563eb", linewidth=2.0, label="Altitude")
    ax.axhline(
        max_altitude,
        color="#dc2626",
        linestyle="--",
        linewidth=1.6,
        label="Altitude limit",
    )
    ax.set_title("Altitude Profile")
    ax.set_xlabel("time [s]")
    ax.set_ylabel("altitude [m]")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def plot_battery(
    rows: List[Dict[str, str]], limits: Dict[str, object], output_path: Path
) -> None:
    time_s = values(rows, "time_s")
    battery = values(rows, "battery_percent")
    min_battery = float(limits["min_battery_percent"])

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.plot(time_s, battery, color="#0891b2", linewidth=2.0, label="Battery")
    ax.axhline(
        min_battery,
        color="#dc2626",
        linestyle="--",
        linewidth=1.6,
        label="Minimum battery",
    )
    ax.set_title("Battery Profile")
    ax.set_xlabel("time [s]")
    ax.set_ylabel("battery [%]")
    ax.set_ylim(0, 105)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def plot_safety_status(rows: List[Dict[str, str]], output_path: Path) -> None:
    time_s = values(rows, "time_s")
    preferred_order = [
        "SAFE",
        "GEOFENCE_WARNING",
        "ALTITUDE_WARNING",
        "GEOFENCE_VIOLATION",
        "ALTITUDE_LIMIT_VIOLATION",
        "LOW_BATTERY",
        "MISSION_TIMEOUT",
        "STATE_TIMEOUT",
    ]
    statuses = [row["safety_status"] for row in rows]
    ordered_statuses = [
        status for status in preferred_order if status in set(statuses)
    ] + sorted(set(statuses) - set(preferred_order))
    status_to_value = {status: index for index, status in enumerate(ordered_statuses)}
    status_values = [status_to_value[status] for status in statuses]

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.step(time_s, status_values, where="post", color="#7c3aed", linewidth=2.0)
    ax.set_title("Safety Status over Time")
    ax.set_xlabel("time [s]")
    ax.set_yticks(list(status_to_value.values()))
    ax.set_yticklabels(list(status_to_value.keys()))
    ax.grid(True, axis="x", alpha=0.3)
    ax.set_ylim(-0.5, max(status_to_value.values()) + 0.5)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def plot_log(input_path: Path, prefix: str, output_dir: Path) -> List[Path]:
    rows = read_log(input_path)
    if not rows:
        raise ValueError("{} is empty".format(input_path))

    output_dir.mkdir(parents=True, exist_ok=True)
    limits = load_limits(CONFIG_PATH)
    outputs = [
        output_dir / "{}_trajectory_plot.png".format(prefix),
        output_dir / "{}_altitude_plot.png".format(prefix),
        output_dir / "{}_battery_plot.png".format(prefix),
        output_dir / "{}_safety_events_plot.png".format(prefix),
    ]

    plot_trajectory(rows, limits, outputs[0])
    plot_altitude(rows, limits, outputs[1])
    plot_battery(rows, limits, outputs[2])
    plot_safety_status(rows, outputs[3])
    return outputs


def default_logs() -> List[Tuple[Path, str]]:
    logs: List[Tuple[Path, str]] = []
    for path in sorted(DATA_DIR.glob("*_mission.csv")):
        prefix = path.stem.replace("_mission", "")
        logs.append((path, prefix))
    return logs


def main() -> None:
    parser = argparse.ArgumentParser(description="Create UAV mission validation plots.")
    parser.add_argument("--input", type=Path, help="CSV mission log to plot.")
    parser.add_argument("--prefix", default="mission", help="Output filename prefix.")
    parser.add_argument(
        "--output-dir", type=Path, default=RESULTS_DIR, help="Directory for PNG plots."
    )
    args = parser.parse_args()

    if args.input:
        logs = [(args.input, args.prefix)]
    else:
        logs = default_logs()
        if not logs:
            raise SystemExit("No logs found. Run `python3 src/main.py` first.")

    for path, prefix in logs:
        outputs = plot_log(path, prefix, args.output_dir)
        print("{} ->".format(path))
        for output in outputs:
            print("  {}".format(output))


if __name__ == "__main__":
    main()
