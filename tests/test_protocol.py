"""Offline protocol regression tests: python -I -m unittest discover tests."""

import ast
from dataclasses import replace
from pathlib import Path
import unittest

from letpot.converters import ISEConverter
from letpot.models import (
    CycleWateringMode,
    LetPotDeviceErrors,
    LetPotWateringSystemStatus,
)

COMPONENT = Path(__file__).parents[1] / "custom_components" / "letpot"


def device_status() -> LetPotWateringSystemStatus:
    """An idle DI-3 configuration with a three-minute manual duration."""
    return LetPotWateringSystemStatus(
        raw=[], pump_mode=0, errors=LetPotDeviceErrors(low_water=False),
        wifi_state=0, pump_on=False, pump_manual_duration=3,
        pump_cycle_on=False, pump_cycle_frequency=24, pump_cycle_duration=3,
        pump_cycle_mode=CycleWateringMode.CONTINUOUS,
        pump_cycle_workinginterval=0, pump_cycle_restinterval=0,
        pump_cycle_skip_water=0, pump_works_end=None,
        pump_works_latest_reason=2, pump_works_latest_time=None,
        pump_works_next_time=None,
    )


class ProtocolTests(unittest.TestCase):
    def test_three_minutes_remains_three_minutes(self) -> None:
        message = ISEConverter("ISE06").get_update_status_message(device_status())
        # Command, operation, mode, cycle flag, then duration MSB/LSB.
        self.assertEqual(message, [65, 2, 0, 0, 0, 3, 0, 24, 0, 3, 0, 0, 0, 0, 0])

    def test_cycle_flag_and_high_bytes_do_not_shift_duration(self) -> None:
        status = replace(
            device_status(), pump_mode=1, pump_manual_duration=257,
            pump_cycle_on=True, pump_cycle_frequency=258, pump_cycle_duration=259,
            pump_cycle_mode=CycleWateringMode.INTERMITTENT,
            pump_cycle_workinginterval=260, pump_cycle_restinterval=261,
        )
        for model in ("ISE05", "ISE06"):
            with self.subTest(model=model):
                message = ISEConverter(model).get_update_status_message(status)
                self.assertEqual(
                    message, [65, 2, 1, 1, 1, 1, 1, 2, 1, 3, 1, 1, 4, 1, 5]
                )

    def test_component_does_not_replace_the_library_encoder(self) -> None:
        for path in COMPONENT.glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text())):
                self.assertFalse(
                    isinstance(node, ast.Attribute)
                    and isinstance(node.ctx, ast.Store)
                    and node.attr == "get_update_status_message",
                    f"{path.name} overrides the library encoder",
                )


if __name__ == "__main__":
    unittest.main()
