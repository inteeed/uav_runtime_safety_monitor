import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def read_log(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def summarize_log(path: Path) -> None:
    rows = read_log(path)
    if not rows:
        print("{}: empty log".format(path))
        return

    duration_s = float(rows[-1]["time_s"])
    violations = [row for row in rows if row["safety_status"] != "SAFE"]
    critical = [row for row in rows if row.get("severity") == "CRITICAL"]
    status_counts = Counter(row["safety_status"] for row in rows)
    severity_counts = Counter(row.get("severity", "UNKNOWN") for row in rows)
    supervisor_counts = Counter(
        row.get("supervisor_mode", "UNKNOWN") for row in rows
    )
    event_path = path.with_name(path.name.replace("_mission.csv", "_events.csv"))
    events = read_log(event_path) if event_path.exists() else []
    responses = [
        row
        for row in rows
        if row.get("active_response", "NONE") not in ("", "NONE", "MONITOR")
    ]

    print("\n{}".format(path))
    print("  samples: {}".format(len(rows)))
    print("  mission duration: {:.1f} s".format(duration_s))
    print("  non-safe samples: {}".format(len(violations)))
    print("  status counts: {}".format(dict(status_counts)))
    print("  severity counts: {}".format(dict(severity_counts)))
    print("  supervisor counts: {}".format(dict(supervisor_counts)))
    print("  event transitions: {}".format(len(events)))

    if violations:
        first = violations[0]
        print(
            "  first non-safe status: {} at t={:.1f} s".format(
                first["safety_status"], float(first["time_s"])
            )
        )
        print("  severity: {}".format(first.get("severity", "UNKNOWN")))
        print("  recommended action: {}".format(first["recommended_action"]))
        print("  detail: {}".format(first["detail"]))
        if critical:
            first_critical = critical[0]
            print(
                "  first critical status: {} at t={:.1f} s".format(
                    first_critical["safety_status"], float(first_critical["time_s"])
                )
            )
            print(
                "  critical action: {}".format(
                    first_critical["recommended_action"]
                )
            )
        if responses:
            first_response = responses[0]
            print(
                "  first supervisor response: {} at t={:.1f} s".format(
                    first_response.get("supervisor_mode", "UNKNOWN"),
                    float(first_response["time_s"]),
                )
            )
            print(
                "  response reason: {}".format(
                    first_response.get("response_reason", "UNKNOWN")
                )
            )
    else:
        print("  result: SAFE")


def existing_logs(paths: Iterable[Path]) -> List[Path]:
    return [path for path in paths if path.exists()]


def default_logs() -> List[Path]:
    return sorted(DATA_DIR.glob("*_mission.csv"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize UAV mission safety logs.")
    parser.add_argument(
        "logs",
        nargs="*",
        type=Path,
        help="CSV log files to analyze. Defaults to data/normal_mission.csv and data/unsafe_mission.csv.",
    )
    args = parser.parse_args()

    logs = args.logs or existing_logs(default_logs())
    if not logs:
        raise SystemExit("No logs found. Run `python3 src/main.py` first.")

    for path in logs:
        summarize_log(path)


if __name__ == "__main__":
    main()
