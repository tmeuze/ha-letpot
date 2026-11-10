"""Dry-run protection for watering systems.

Pure functions (no Home Assistant imports) so the policy is unit-testable offline.

The only dry signal the device exposes is its low-water flag (status byte 7, bit 0),
which the library maps to `errors.low_water`. Unknown (None/missing) is treated as
"not dry": the guard fails open rather than blocking watering on a missing signal.
"""

from letpot.models import LetPotWateringSystemStatus, WateringReason

# Seconds between protective stop commands while the device keeps reporting a
# running pump with low water, so a slow device is not flooded with writes.
STOP_RETRY_SECONDS = 15


def is_dry(status: object) -> bool:
    """Return True if a watering system reports low water."""
    return isinstance(status, LetPotWateringSystemStatus) and bool(
        status.errors.low_water
    )


def is_pumping(status: LetPotWateringSystemStatus) -> bool:
    """Return True if the pump is running or a manual run is requested."""
    return status.pump_on or status.pump_mode > 0


def should_block_start(status: object, protection_enabled: bool) -> bool:
    """Return True if a manual or cycle start must be refused."""
    return protection_enabled and is_dry(status)


def protective_stop_changes(
    status: object, protection_enabled: bool
) -> dict[str, object] | None:
    """Return status field changes that stop a dry pump, or None if no stop is needed.

    A run started by the cycle/schedule is only interrupted by disabling the cycle
    (the device records that as "cycle disabled while running"), so the cycle flag is
    cleared in that case. A manual run is stopped by clearing the pump mode alone.
    """
    if not (
        protection_enabled
        and is_dry(status)
        and isinstance(status, LetPotWateringSystemStatus)
        and is_pumping(status)
    ):
        return None
    changes: dict[str, object] = {"pump_mode": 0}
    if status.pump_cycle_on and status.pump_works_latest_reason in (
        WateringReason.CYCLE,
        WateringReason.SCHEDULED,
    ):
        changes["pump_cycle_on"] = False
    return changes
