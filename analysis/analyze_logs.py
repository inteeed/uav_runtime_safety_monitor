import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOGS = [
    PROJECT_ROOT / "data" / "normal_mission.csv",
    PROJECT_ROOT / "data" / "unsafe_mission.csv",
]


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
    status_counts = Counter(row["safety_status"] for row in rows)

    print("\n{}".format(path))
    print("  samples: {}".format(len(rows)))
    print("  mission duration: {:.1f} s".format(duration_s))
    print("  safety violations: {}".format(len(violations)))
    print("  status counts: {}".format(dict(status_counts)))

    if violations:
        first = violations[0]
        print(
            "  first violation: {} at t={:.1f} s".format(
                first["safety_status"], float(first["time_s"])
            )
        )
        print("  recommended action: {}".format(first["recommended_action"]))
        print("  detail: {}".format(first["detail"]))
    else:
        print("  result: SAFE")


def existing_logs(paths: Iterable[Path]) -> List[Path]:
    return [path for path in paths if path.exists()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize UAV mission safety logs.")
    parser.add_argument(
        "logs",
        nargs="*",
        type=Path,
        help="CSV log files to analyze. Defaults to data/normal_mission.csv and data/unsafe_mission.csv.",
    )
    args = parser.parse_args()

    logs = args.logs or existing_logs(DEFAULT_LOGS)
    if not logs:
        raise SystemExit("No logs found. Run `python3 src/main.py` first.")

    for path in logs:
        summarize_log(path)


if __name__ == "__main__":
    main()

