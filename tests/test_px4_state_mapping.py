import math
import unittest

from uav_runtime_safety_monitor.px4_state_mapping import (
    battery_percent_from_px4_remaining,
    finite_float,
    local_position_to_uav_state,
)


class FakeLocalPosition:
    x = 12.5
    y = -4.0
    z = -18.0
    vx = 3.0
    vy = -1.5
    vz = 0.5


class PX4StateMappingTest(unittest.TestCase):
    def test_converts_ned_position_to_positive_up_altitude(self) -> None:
        state = local_position_to_uav_state(
            FakeLocalPosition(),
            time_s=4.25,
            battery_percent=72.0,
        )

        self.assertEqual(state.frame_id, "px4_local_ned_converted")
        self.assertEqual(state.x_m, 12.5)
        self.assertEqual(state.y_m, -4.0)
        self.assertEqual(state.z_m, 18.0)
        self.assertEqual(state.vx_mps, 3.0)
        self.assertEqual(state.vy_mps, -1.5)
        self.assertEqual(state.vz_mps, -0.5)
        self.assertEqual(state.battery_percent, 72.0)

    def test_battery_remaining_fraction_to_percent(self) -> None:
        self.assertEqual(battery_percent_from_px4_remaining(0.42, 100.0), 42.0)

    def test_battery_remaining_percent_is_preserved(self) -> None:
        self.assertEqual(battery_percent_from_px4_remaining(65.0, 100.0), 65.0)

    def test_invalid_battery_uses_fallback(self) -> None:
        self.assertEqual(
            battery_percent_from_px4_remaining(math.nan, 88.0),
            88.0,
        )

    def test_finite_float_rejects_nan(self) -> None:
        self.assertEqual(finite_float(math.nan, 3.0), 3.0)


if __name__ == "__main__":
    unittest.main()
