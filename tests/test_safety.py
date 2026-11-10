"""Offline checks for dry-run protection: python -I -m unittest discover tests."""

from dataclasses import replace
from pathlib import Path
import sys
import unittest

from letpot.models import LetPotDeviceErrors, WateringReason

sys.path.insert(0, str(Path(__file__).parents[1] / "custom_components" / "letpot"))

from safety import is_dry, protective_stop_changes, should_block_start
from test_protocol import device_status


def dry(**kwargs):
    return replace(device_status(), errors=LetPotDeviceErrors(low_water=True), **kwargs)


class DryRunTests(unittest.TestCase):
    def test_is_dry_only_when_low_water_reported(self):
        self.assertTrue(is_dry(dry()))
        self.assertFalse(is_dry(device_status()))
        unknown = replace(device_status(), errors=LetPotDeviceErrors(low_water=None))
        self.assertFalse(is_dry(unknown))
        self.assertFalse(is_dry(None))
        self.assertFalse(is_dry(object()))

    def test_start_blocked_only_when_dry_and_enabled(self):
        self.assertTrue(should_block_start(dry(), True))
        self.assertFalse(should_block_start(dry(), False))
        self.assertFalse(should_block_start(device_status(), True))

    def test_no_stop_when_water_present_or_pump_idle_or_disabled(self):
        running = replace(device_status(), pump_on=True, pump_mode=1)
        self.assertIsNone(protective_stop_changes(running, True))
        self.assertIsNone(protective_stop_changes(dry(), True))
        self.assertIsNone(protective_stop_changes(dry(pump_on=True), False))

    def test_manual_run_stopped_by_clearing_pump_mode_only(self):
        status = dry(pump_on=True, pump_mode=1, pump_cycle_on=True,
                     pump_works_latest_reason=WateringReason.MANUAL)
        self.assertEqual(protective_stop_changes(status, True), {"pump_mode": 0})

    def test_requested_mode_without_pump_on_is_also_stopped(self):
        self.assertEqual(protective_stop_changes(dry(pump_mode=1), True), {"pump_mode": 0})

    def test_cycle_or_scheduled_run_also_clears_cycle_flag(self):
        for reason in (WateringReason.CYCLE, WateringReason.SCHEDULED):
            with self.subTest(reason=reason):
                status = dry(pump_on=True, pump_cycle_on=True,
                             pump_works_latest_reason=reason)
                self.assertEqual(
                    protective_stop_changes(status, True),
                    {"pump_mode": 0, "pump_cycle_on": False},
                )

    def test_cycle_flag_untouched_when_cycle_is_off(self):
        status = dry(pump_on=True, pump_cycle_on=False,
                     pump_works_latest_reason=WateringReason.CYCLE)
        self.assertEqual(protective_stop_changes(status, True), {"pump_mode": 0})


if __name__ == "__main__":
    unittest.main()
