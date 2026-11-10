from collections.abc import Callable, Coroutine
import dataclasses
from dataclasses import dataclass
from typing import Any, override

from letpot.deviceclient import LetPotDeviceClient
from letpot.models import (
    DeviceFeature,
    LetPotDeviceStatus,
    LetPotGardenStatus,
    LetPotWateringSystemStatus,
)

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import LetPotConfigEntry, LetPotDeviceCoordinator
from .const import DOMAIN
from .safety import should_block_start
from .watering import async_update_watering
from .entity import LetPotEntity, LetPotEntityDescription, exception_handler

# Each change pushes a 'full' device status with the change. The library will cache
# pending changes to avoid overwriting, but try to avoid a lot of parallelism.
PARALLEL_UPDATES = 1

# Switches that start the pump and are refused while the device reports low water.
DRY_RUN_GUARDED = frozenset({"pump", "pump_cycle"})


@dataclass(frozen=True, kw_only=True)
class LetPotSwitchEntityDescription[_DataT: LetPotDeviceStatus](
    LetPotEntityDescription, SwitchEntityDescription
):
    """Describes a LetPot switch entity."""

    value_fn: Callable[[_DataT], bool | None]
    set_value_fn: Callable[[LetPotDeviceClient, str, bool], Coroutine[Any, Any, None]]


SWITCHES: tuple[LetPotSwitchEntityDescription[LetPotDeviceStatus], ...] = (
    LetPotSwitchEntityDescription[LetPotDeviceStatus](
        key="alarm_sound",
        translation_key="alarm_sound",
        value_fn=lambda status: status.system_sound if isinstance(status, LetPotGardenStatus) else None,
        set_value_fn=(
            lambda device_client, serial, value: device_client.set_sound(serial, value)
        ),
        entity_category=EntityCategory.CONFIG,
        supported_fn=lambda coordinator: isinstance(coordinator.data, LetPotGardenStatus) and coordinator.data.system_sound is not None,
    ),
    LetPotSwitchEntityDescription[LetPotDeviceStatus](
        key="auto_mode",
        translation_key="auto_mode",
        value_fn=lambda status: (status.water_mode == 1) if isinstance(status, LetPotGardenStatus) else False,
        set_value_fn=(
            lambda device_client, serial, value: device_client.set_water_mode(
                serial, value
            )
        ),
        entity_category=EntityCategory.CONFIG,
        supported_fn=(
            lambda coordinator: (
                isinstance(coordinator.data, LetPotGardenStatus) and
                DeviceFeature.PUMP_AUTO
                in coordinator.device_client.device_info(
                    coordinator.device.serial_number
                ).features
            )
        ),
    ),
    LetPotSwitchEntityDescription[LetPotDeviceStatus](
        key="power",
        translation_key="power",
        value_fn=lambda status: status.system_on if isinstance(status, LetPotGardenStatus) else False,
        set_value_fn=lambda device_client, serial, value: device_client.set_power(
            serial, value
        ),
        entity_category=EntityCategory.CONFIG,
        supported_fn=lambda coordinator: isinstance(coordinator.data, LetPotGardenStatus),
    ),
    LetPotSwitchEntityDescription[LetPotDeviceStatus](
        key="pump_cycling",
        translation_key="pump_cycling",
        value_fn=lambda status: (status.pump_mode == 1) if isinstance(status, LetPotGardenStatus) else False,
        set_value_fn=lambda device_client, serial, value: device_client.set_pump_mode(
            serial, value
        ),
        entity_category=EntityCategory.CONFIG,
        supported_fn=lambda coordinator: isinstance(coordinator.data, LetPotGardenStatus),
    ),
    LetPotSwitchEntityDescription[LetPotDeviceStatus](
        key="pump",
        translation_key="pump",
        value_fn=lambda status: status.pump_on if isinstance(status, LetPotWateringSystemStatus) else False,
        set_value_fn=lambda device_client, serial, value: async_update_watering(
            device_client, serial, pump_mode=1 if value else 0
        ),
        supported_fn=lambda coordinator: isinstance(coordinator.data, LetPotWateringSystemStatus),
    ),
    LetPotSwitchEntityDescription[LetPotDeviceStatus](
        key="pump_cycle",
        translation_key="pump_cycle",
        value_fn=lambda status: status.pump_cycle_on if isinstance(status, LetPotWateringSystemStatus) else None,
        set_value_fn=lambda device_client, serial, value: async_update_watering(
            device_client, serial, pump_cycle_on=value
        ),
        entity_category=EntityCategory.CONFIG,
        supported_fn=lambda coordinator: isinstance(coordinator.data, LetPotWateringSystemStatus),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LetPotConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up LetPot switch entities."""
    coordinators = entry.runtime_data
    entities: list[SwitchEntity] = [
        LetPotSwitchEntity[LetPotDeviceStatus](coordinator, description)
        for description in SWITCHES
        for coordinator in coordinators
        if description.supported_fn(coordinator)
    ]
    entities.extend(
        LetPotDryRunProtectionSwitch(coordinator)
        for coordinator in coordinators
        if isinstance(coordinator.data, LetPotWateringSystemStatus)
    )
    async_add_entities(entities)


class LetPotSwitchEntity[_DataT: LetPotDeviceStatus](
    LetPotEntity[_DataT], SwitchEntity
):
    """Defines a LetPot switch entity."""

    entity_description: LetPotSwitchEntityDescription[_DataT]

    def __init__(
        self,
        coordinator: LetPotDeviceCoordinator[_DataT],
        description: LetPotSwitchEntityDescription[_DataT],
    ) -> None:
        """Initialize LetPot switch entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = (
            f"{coordinator.config_entry.unique_id}"
            f"_{coordinator.device.serial_number}"
            f"_{description.key}"
        )

    @property
    @override
    def is_on(self) -> bool | None:
        """Return if the entity is on."""
        return self.entity_description.value_fn(self.coordinator.data)

    @exception_handler
    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        if self.entity_description.key in DRY_RUN_GUARDED and should_block_start(
            self.coordinator.data, self.coordinator.dry_run_protection
        ):
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="dry_run_blocked"
            )
        await self.entity_description.set_value_fn(
            self.coordinator.device_client, self.coordinator.device.serial_number, True
        )

    @exception_handler
    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.entity_description.set_value_fn(
            self.coordinator.device_client, self.coordinator.device.serial_number, False
        )


class LetPotDryRunProtectionSwitch(LetPotEntity, SwitchEntity, RestoreEntity):
    """Configuration switch for dry-run protection (on by default)."""

    _attr_translation_key = "dry_run_protection"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: LetPotDeviceCoordinator) -> None:
        """Initialize the dry-run protection switch."""
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{coordinator.config_entry.unique_id}"
            f"_{coordinator.device.serial_number}"
            "_dry_run_protection"
        )

    @override
    async def async_added_to_hass(self) -> None:
        """Restore the last chosen state; default is protection on."""
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            self.coordinator.dry_run_protection = last.state != "off"

    @property
    @override
    def is_on(self) -> bool:
        """Return if dry-run protection is enabled."""
        return self.coordinator.dry_run_protection

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable dry-run protection."""
        self.coordinator.dry_run_protection = True
        self.async_write_ha_state()

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable dry-run protection."""
        self.coordinator.dry_run_protection = False
        self.async_write_ha_state()
