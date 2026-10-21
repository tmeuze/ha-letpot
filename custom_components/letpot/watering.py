"""Watering system (ISE05/ISE06) support helpers.

python-letpot 0.7.0 can read watering system status, but only exposes
`set_pump_mode` for writing. These helpers cover the remaining settings until the
library gains public setters. Writes use the library's own message encoder: do not
override it (an earlier override with the duration bytes before the cycle flag
corrupted the stored manual duration on a DI-3).
"""

import dataclasses
from typing import Any

from letpot.deviceclient import LetPotDeviceClient


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
