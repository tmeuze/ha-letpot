"""Watering system (ISE05/ISE06) support helpers.

python-letpot 0.7.0 can read watering system status, but only exposes
`set_pump_mode` for writing. These helpers cover the remaining settings until the
library gains public setters.
"""

import dataclasses
import math
from typing import Any

from letpot.converters import ISEConverter
from letpot.deviceclient import LetPotDeviceClient
from letpot.exceptions import LetPotDeviceCategoryException
from letpot.models import LetPotDeviceStatus, LetPotWateringSystemStatus


def _patched_get_update_status_message(
    self: ISEConverter, status: LetPotDeviceStatus
) -> list[int]:
    """Build the ISE update message with the manual duration before the cycle flag.

    Library 0.7.0 places the cycle flag before the manual duration; the community
    DI-3 fix reports that this corrupts values on write. UNVERIFIED against a
    packet capture, so keep it isolated here and drop it once resolved upstream.
    """
    if not isinstance(status, LetPotWateringSystemStatus):
        raise LetPotDeviceCategoryException
    return [
        65,
        2,
        1 if status.pump_mode > 0 else 0,
        math.floor((status.pump_manual_duration or 0) / 256),
        (status.pump_manual_duration or 0) % 256,
        1 if status.pump_cycle_on is True else 0,
        math.floor((status.pump_cycle_frequency or 0) / 256),
        (status.pump_cycle_frequency or 0) % 256,
        math.floor((status.pump_cycle_duration or 0) / 256),
        (status.pump_cycle_duration or 0) % 256,
        status.pump_cycle_mode or 0,
        math.floor((status.pump_cycle_workinginterval or 0) / 256),
        (status.pump_cycle_workinginterval or 0) % 256,
        math.floor((status.pump_cycle_restinterval or 0) / 256),
        (status.pump_cycle_restinterval or 0) % 256,
    ]


def apply_protocol_patch() -> None:
    """Apply the write message patch (idempotent)."""
    ISEConverter.get_update_status_message = _patched_get_update_status_message  # type: ignore[method-assign]


async def async_update_watering(
    device_client: LetPotDeviceClient, serial: str, **changes: Any
) -> None:
    """Publish the current watering system status with the given fields changed.

    Uses the library's private publish helpers, which also handle pending-status
    caching so quick successive changes don't overwrite each other.
    """
    status = device_client._get_publish_status(serial)  # noqa: SLF001
    await device_client._publish_status(  # noqa: SLF001
        serial, dataclasses.replace(status, **changes)
    )
