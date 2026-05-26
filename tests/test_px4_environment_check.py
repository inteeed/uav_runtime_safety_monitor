import os
import unittest

from uav_runtime_safety_monitor.px4_environment_check import (
    FAIL,
    INFO,
    OK,
    WARN,
    contains_noetic_path,
    evaluate_current_shell,
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
        self.assertEqual(parse_lines("\npx4_msgs\n\nstd_msgs\n"), ["px4_msgs", "std_msgs"])


if __name__ == "__main__":
    unittest.main()
