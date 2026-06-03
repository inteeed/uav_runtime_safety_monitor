import unittest

from uav_safety_core.constants import ActiveResponse
from uav_safety_core.px4_commands import (
    CMD_LAND,
    CMD_RETURN_TO_LAUNCH,
    command_for_response,
)


class PX4CommandMappingTest(unittest.TestCase):
    def test_return_to_home_maps_to_rtl(self) -> None:
        self.assertEqual(
            command_for_response(ActiveResponse.RETURN_TO_HOME),
            CMD_RETURN_TO_LAUNCH,
        )

    def test_land_maps_to_land(self) -> None:
        self.assertEqual(command_for_response(ActiveResponse.LAND), CMD_LAND)

    def test_monitor_only_response_has_no_command(self) -> None:
        self.assertIsNone(command_for_response(ActiveResponse.MONITOR))
        self.assertIsNone(command_for_response(ActiveResponse.NONE))


if __name__ == "__main__":
    unittest.main()
