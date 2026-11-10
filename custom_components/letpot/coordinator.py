"""Coordinator for the LetPot integration."""

import asyncio
from collections.abc import Callable
from datetime import timedelta
import logging
import time
from typing import cast, override

from letpot.deviceclient import LetPotDeviceClient
from letpot.exceptions import LetPotAuthenticationException, LetPotException
from letpot.models import LetPotDevice, LetPotDeviceStatus

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import REQUEST_UPDATE_TIMEOUT
from .safety import STOP_RETRY_SECONDS, protective_stop_changes
from .watering import async_update_watering

_LOGGER = logging.getLogger(__name__)

type LetPotConfigEntry = ConfigEntry[list[LetPotDeviceCoordinator[LetPotDeviceStatus]]]


class LetPotDeviceCoordinator[_DataT: LetPotDeviceStatus](
    DataUpdateCoordinator[_DataT]
):
    """Class to handle data updates for a specific device."""

    config_entry: LetPotConfigEntry

    device: LetPotDevice
    device_client: LetPotDeviceClient

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: LetPotConfigEntry,
        device: LetPotDevice,
        device_client: LetPotDeviceClient,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"LetPot {device.serial_number}",
            update_interval=timedelta(minutes=10),
        )
        self.device = device
        self.device_client = device_client
        # Refuse/stop watering when the device reports low water (watering systems).
        self.dry_run_protection = True
        self._last_protective_stop = 0.0

    def _handle_status_update(self, status: _DataT) -> None:
        """Distribute status update to entities."""
        self.async_set_updated_data(data=status)
        if protective := protective_stop_changes(status, self.dry_run_protection):
            now = time.monotonic()
            if now - self._last_protective_stop >= STOP_RETRY_SECONDS:
                self._last_protective_stop = now
                self.config_entry.async_create_background_task(
                    self.hass,
                    self._async_protective_stop(protective),
                    name=f"letpot dry-run stop {self.device.serial_number}",
                )

    async def _async_protective_stop(self, changes: dict[str, object]) -> None:
        """Stop a pump that is running with the water tank reported empty."""
        _LOGGER.warning(
            "%s reports low water while pumping; stopping the pump (%s)",
            self.device.serial_number,
            ", ".join(f"{k}={v}" for k, v in changes.items()),
        )
        try:
            await async_update_watering(
                self.device_client, self.device.serial_number, **changes
            )
        except LetPotException:
            _LOGGER.exception("Failed to stop pump on low water; retrying on next update")

    @override
    async def _async_setup(self) -> None:
        """Set up subscription for coordinator."""
        try:
            await self.device_client.subscribe(
                self.device.serial_number,
                cast(Callable[[LetPotDeviceStatus], None], self._handle_status_update),
            )
        except LetPotAuthenticationException as exc:
            raise ConfigEntryAuthFailed from exc

    @override
    async def _async_update_data(self) -> _DataT:
        """Request an update from the device and wait for a status update or timeout."""
        try:
            async with asyncio.timeout(REQUEST_UPDATE_TIMEOUT):
                await self.device_client.get_current_status(self.device.serial_number)
        except LetPotException as exc:
            raise UpdateFailed(exc) from exc

        # The subscription task will have updated coordinator.data, so return that data.
        # If we don't return anything here, coordinator.data will be set to None.
        return self.data
