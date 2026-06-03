from dataclasses import dataclass
import argparse
import os
from pathlib import Path
import shutil
import subprocess
from typing import Iterable, List, Mapping, Optional, Sequence


OK = "OK"
WARN = "WARN"
FAIL = "FAIL"
INFO = "INFO"

# The project was developed on ROS2 Foxy but is distro-agnostic. Override the
# expected distribution (e.g. for Humble) with the EXPECTED_ROS_DISTRO env var
# or the --expected-distro flag.
DEFAULT_EXPECTED_DISTRO = os.environ.get("EXPECTED_ROS_DISTRO", "foxy")
DEFAULT_ROS_SETUP = "/opt/ros/{}/setup.bash".format(DEFAULT_EXPECTED_DISTRO)
PX4_ROS2_PACKAGES = ("px4_msgs",)
PX4_REQUIRED_TELEMETRY_TOPICS = (
    "/fmu/out/vehicle_local_position",
)
PX4_OPTIONAL_TELEMETRY_TOPICS = (
    "/fmu/out/battery_status",
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str
    recommendation: str = ""

    @property
    def is_failure(self) -> bool:
        return self.status == FAIL


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def contains_noetic_path(value: str) -> bool:
    return any(part for part in value.split(os.pathsep) if "/noetic" in part)


def noetic_contamination(environ: Mapping[str, str]) -> List[str]:
    contaminated = []
    for name in (
        "ROS_DISTRO",
        "ROS_PACKAGE_PATH",
        "CMAKE_PREFIX_PATH",
        "PYTHONPATH",
        "LD_LIBRARY_PATH",
        "PATH",
    ):
        value = environ.get(name, "")
        if name == "ROS_DISTRO" and value == "noetic":
            contaminated.append(name)
        elif contains_noetic_path(value):
            contaminated.append(name)
    return contaminated


def evaluate_current_shell(
    environ: Mapping[str, str],
    expected_distro: str = DEFAULT_EXPECTED_DISTRO,
) -> CheckResult:
    contaminated = noetic_contamination(environ)
    if contaminated:
        return CheckResult(
            "current_shell",
            FAIL,
            "ROS Noetic content found in: {}".format(", ".join(contaminated)),
            "Open a clean terminal before sourcing ROS2, or run with env -i.",
        )

    ros_distro = environ.get("ROS_DISTRO")
    if ros_distro and ros_distro != expected_distro:
        return CheckResult(
            "current_shell",
            WARN,
            "ROS_DISTRO is set to {!r} instead of {!r}.".format(
                ros_distro, expected_distro
            ),
            "Use a clean ROS2 {} shell for this repository.".format(expected_distro),
        )

    if ros_distro == expected_distro:
        return CheckResult(
            "current_shell",
            OK,
            "ROS2 {} environment detected.".format(expected_distro),
        )

    return CheckResult(
        "current_shell",
        INFO,
        "No ROS distribution is currently sourced.",
        "Source /opt/ros/{}/setup.bash before running ROS2 nodes.".format(
            expected_distro
        ),
    )


def evaluate_command(name: str, executable: str) -> CheckResult:
    path = shutil.which(executable)
    if path:
        return CheckResult(name, OK, "{} found at {}".format(executable, path))

    return CheckResult(
        name,
        WARN,
        "{} is not on PATH.".format(executable),
        "Install/source the tool before running live PX4 SITL validation.",
    )


def run_shell(command: str, timeout_s: float = 30.0) -> CommandResult:
    completed = subprocess.run(
        ["bash", "-lc", command],
        check=False,
        text=True,
        capture_output=True,
        timeout=timeout_s,
    )
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def source_and_run(
    setup_files: Sequence[Path],
    command: str,
    timeout_s: float = 30.0,
) -> CommandResult:
    source_prefix = "; ".join("source {}".format(path) for path in setup_files)
    shell_command = "{}; {}".format(source_prefix, command)
    return run_shell(shell_command, timeout_s=timeout_s)


def evaluate_ros_setup(
    ros_setup: Path,
    expected_distro: str = DEFAULT_EXPECTED_DISTRO,
) -> CheckResult:
    if not ros_setup.exists():
        return CheckResult(
            "ros_setup",
            FAIL,
            "{} does not exist.".format(ros_setup),
            "Install ROS2 {} or pass --ros-setup to the correct setup.bash.".format(
                expected_distro
            ),
        )

    result = source_and_run([ros_setup], "printenv ROS_DISTRO", timeout_s=10.0)
    distro = result.stdout.strip()
    if result.returncode != 0:
        return CheckResult(
            "ros_setup",
            FAIL,
            "Could not source {}.".format(ros_setup),
            result.stderr.strip(),
        )

    if distro != expected_distro:
        return CheckResult(
            "ros_setup",
            WARN,
            "Sourcing {} sets ROS_DISTRO={!r} (expected {!r}).".format(
                ros_setup, distro, expected_distro
            ),
            "Set EXPECTED_ROS_DISTRO or --expected-distro to match your install.",
        )

    return CheckResult(
        "ros_setup", OK, "{} sources ROS2 {}.".format(ros_setup, expected_distro)
    )


def parse_lines(output: str) -> List[str]:
    return [line.strip() for line in output.splitlines() if line.strip()]


def evaluate_ros_packages(
    setup_files: Sequence[Path],
    required_packages: Sequence[str] = PX4_ROS2_PACKAGES,
) -> CheckResult:
    missing_setups = [str(path) for path in setup_files if not path.exists()]
    if missing_setups:
        return CheckResult(
            "ros_packages",
            FAIL,
            "Setup file(s) missing: {}".format(", ".join(missing_setups)),
        )

    result = source_and_run(setup_files, "ros2 pkg list", timeout_s=30.0)
    if result.returncode != 0:
        return CheckResult(
            "ros_packages",
            FAIL,
            "Could not list ROS2 packages.",
            result.stderr.strip(),
        )

    available = set(parse_lines(result.stdout))
    missing = [package for package in required_packages if package not in available]
    if missing:
        return CheckResult(
            "ros_packages",
            FAIL,
            "Missing ROS2 package(s): {}".format(", ".join(missing)),
            "Build/source a PX4 ROS2 workspace containing px4_msgs.",
        )

    return CheckResult(
        "ros_packages",
        OK,
        "Found required ROS2 package(s): {}".format(", ".join(required_packages)),
    )


def evaluate_ros_topics(
    setup_files: Sequence[Path],
    required_topics: Sequence[str] = PX4_REQUIRED_TELEMETRY_TOPICS,
    optional_topics: Sequence[str] = PX4_OPTIONAL_TELEMETRY_TOPICS,
    require_optional_topics: bool = False,
) -> CheckResult:
    missing_setups = [str(path) for path in setup_files if not path.exists()]
    if missing_setups:
        return CheckResult(
            "px4_topics",
            FAIL,
            "Setup file(s) missing: {}".format(", ".join(missing_setups)),
        )

    result = source_and_run(setup_files, "ros2 topic list", timeout_s=15.0)
    if result.returncode != 0:
        return CheckResult(
            "px4_topics",
            FAIL,
            "Could not list ROS2 topics.",
            result.stderr.strip(),
        )

    available = set(parse_lines(result.stdout))
    missing = [topic for topic in required_topics if topic not in available]
    if missing:
        return CheckResult(
            "px4_topics",
            FAIL,
            "Missing PX4 telemetry topic(s): {}".format(", ".join(missing)),
            "Start PX4 SITL and the Micro XRCE-DDS Agent, then rerun with --check-topics.",
        )

    missing_optional = [topic for topic in optional_topics if topic not in available]
    if missing_optional and require_optional_topics:
        return CheckResult(
            "px4_topics",
            FAIL,
            "Missing optional PX4 telemetry topic(s) required by this run: {}".format(
                ", ".join(missing_optional)
            ),
            "Use a PX4 SITL setup that publishes these topics, or omit --require-battery-topic.",
        )

    if missing_optional:
        return CheckResult(
            "px4_topics",
            WARN,
            "Found required PX4 telemetry topic(s): {}. Optional topic(s) not visible: {}".format(
                ", ".join(required_topics),
                ", ".join(missing_optional),
            ),
            "The PX4 state bridge will use fallback values for missing optional telemetry.",
        )

    return CheckResult(
        "px4_topics",
        OK,
        "Found PX4 telemetry topic(s): {}".format(
            ", ".join([*required_topics, *optional_topics])
        ),
    )


def collect_checks(
    environ: Mapping[str, str],
    ros_setup: Path,
    extra_setups: Sequence[Path] = (),
    check_topics: bool = False,
    require_battery_topic: bool = False,
    expected_distro: str = DEFAULT_EXPECTED_DISTRO,
) -> List[CheckResult]:
    setup_files = [ros_setup, *extra_setups]
    checks = [
        evaluate_current_shell(environ, expected_distro=expected_distro),
        evaluate_ros_setup(ros_setup, expected_distro=expected_distro),
        evaluate_command("px4_command", "px4"),
        evaluate_command("micro_xrce_agent", "MicroXRCEAgent"),
        evaluate_ros_packages(setup_files),
    ]

    if check_topics:
        checks.append(
            evaluate_ros_topics(
                setup_files,
                require_optional_topics=require_battery_topic,
            )
        )
    else:
        checks.append(
            CheckResult(
                "px4_topics",
                INFO,
                "Topic check skipped.",
                "Run again with --check-topics after PX4 SITL is running.",
            )
        )

    return checks


def format_result(result: CheckResult) -> str:
    line = "{:<5} {:<18} {}".format(result.status, result.name, result.detail)
    if result.recommendation:
        line += "\n      -> {}".format(result.recommendation)
    return line


def print_results(results: Iterable[CheckResult]) -> None:
    print("PX4 SITL readiness check")
    print("-" * 78)
    for result in results:
        print(format_result(result))
    print("-" * 78)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check whether the local shell is ready for PX4 ROS2 telemetry."
    )
    parser.add_argument(
        "--ros-setup",
        default=DEFAULT_ROS_SETUP,
        help="Path to the ROS2 setup.bash file to source for checks.",
    )
    parser.add_argument(
        "--expected-distro",
        default=DEFAULT_EXPECTED_DISTRO,
        help=(
            "ROS2 distribution this run expects (default from EXPECTED_ROS_DISTRO "
            "or 'foxy'). Set to 'humble' etc. when running on a newer distro."
        ),
    )
    parser.add_argument(
        "--check-topics",
        action="store_true",
        help="Also require live PX4 telemetry topics to be visible.",
    )
    parser.add_argument(
        "--require-battery-topic",
        action="store_true",
        help=(
            "Fail the live topic check if /fmu/out/battery_status is missing. "
            "By default this topic is optional because PX4 SIH SITL may omit it."
        ),
    )
    parser.add_argument(
        "--extra-setup",
        action="append",
        default=[],
        help=(
            "Additional workspace setup.bash to source for px4_msgs. "
            "Can be passed more than once."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code when any check fails.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    extra_setups = [Path(path).expanduser() for path in args.extra_setup]
    env_px4_setup = os.environ.get("PX4_ROS2_WS_SETUP")
    if env_px4_setup:
        extra_setups.append(Path(env_px4_setup).expanduser())

    results = collect_checks(
        os.environ,
        Path(args.ros_setup).expanduser(),
        extra_setups=extra_setups,
        check_topics=args.check_topics,
        require_battery_topic=args.require_battery_topic,
        expected_distro=args.expected_distro,
    )
    print_results(results)

    if args.strict and any(result.is_failure for result in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
