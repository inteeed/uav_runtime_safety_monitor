import os
from pathlib import Path
import unittest
from unittest.mock import patch

from uav_runtime_safety_monitor.px4_environment_check import (
    CommandResult,
    FAIL,
    INFO,
    OK,
    WARN,
    contains_noetic_path,
    evaluate_current_shell,
    evaluate_ros_topics,
    parse_lines,
)


class PX4EnvironmentCheckTest(unittest.TestCase):
    def test_detects_noetic_path(self) -> None:
        value = os.pathsep.join(
            [
                "/opt/ros/foxy/lib/python3.8/site-packages",
                "/opt/ros/noetic/lib/python3/dist-packages",
            ]
        )

        self.assertTrue(contains_noetic_path(value))

    def test_accepts_clean_foxy_shell(self) -> None:
        result = evaluate_current_shell({"ROS_DISTRO": "foxy"})

        self.assertEqual(result.status, OK)

    def test_rejects_noetic_shell(self) -> None:
        result = evaluate_current_shell({"ROS_DISTRO": "noetic"})

        self.assertEqual(result.status, FAIL)

    def test_warns_on_other_ros2_distribution(self) -> None:
        result = evaluate_current_shell({"ROS_DISTRO": "humble"})

        self.assertEqual(result.status, WARN)

    def test_reports_unsourced_shell_as_info(self) -> None:
        result = evaluate_current_shell({})

        self.assertEqual(result.status, INFO)

    def test_parse_lines_ignores_blank_lines(self) -> None:
        self.assertEqual(
            parse_lines("\npx4_msgs\n\nstd_msgs\n"),
            ["px4_msgs", "std_msgs"],
        )

    def test_topic_check_accepts_sih_without_battery_topic(self) -> None:
        output = "/fmu/out/vehicle_local_position\n/fmu/out/vehicle_status\n"

        with patch(
            "uav_runtime_safety_monitor.px4_environment_check.source_and_run",
            return_value=CommandResult(0, output, ""),
        ):
            result = evaluate_ros_topics([Path("/")])

        self.assertEqual(result.status, WARN)
        self.assertIn("/fmu/out/battery_status", result.detail)

    def test_topic_check_can_require_battery_topic(self) -> None:
        output = "/fmu/out/vehicle_local_position\n/fmu/out/vehicle_status\n"

        with patch(
            "uav_runtime_safety_monitor.px4_environment_check.source_and_run",
            return_value=CommandResult(0, output, ""),
        ):
            result = evaluate_ros_topics(
                [Path("/")],
                require_optional_topics=True,
            )

        self.assertEqual(result.status, FAIL)

    def test_topic_check_fails_without_local_position(self) -> None:
        output = "/fmu/out/vehicle_status\n/fmu/out/battery_status\n"

        with patch(
            "uav_runtime_safety_monitor.px4_environment_check.source_and_run",
            return_value=CommandResult(0, output, ""),
        ):
            result = evaluate_ros_topics([Path("/")])

        self.assertEqual(result.status, FAIL)


if __name__ == "__main__":
    unittest.main()
