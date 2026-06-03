import csv
import tempfile
import unittest
from pathlib import Path

from uav_safety_core.constants import ActiveResponse
from uav_safety_core.px4_commands import (
    CMD_LAND,
    CMD_RETURN_TO_LAUNCH,
    append_command_record,
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


class AppendCommandRecordTest(unittest.TestCase):
    def test_writes_header_then_appends_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "px4_command_log.csv"
            append_command_record(path, 31.4, ActiveResponse.RETURN_TO_HOME,
                                  CMD_RETURN_TO_LAUNCH)
            append_command_record(path, 40.0, ActiveResponse.LAND, CMD_LAND)

            with path.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["active_response"], "RETURN_TO_HOME")
            self.assertEqual(rows[0]["command"], str(CMD_RETURN_TO_LAUNCH))
            self.assertEqual(rows[1]["command"], str(CMD_LAND))


if __name__ == "__main__":
    unittest.main()
