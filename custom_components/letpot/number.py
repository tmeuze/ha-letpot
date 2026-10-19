"""Support for LetPot number entities."""

from collections.abc import Callable, Coroutine
import dataclasses
from dataclasses import dataclass
from typing import Any, override

from letpot.deviceclient import LetPotDeviceClient
from letpot.models import DeviceFeature, LetPotDeviceStatus, LetPotGardenStatus, LetPotWateringSystemStatus

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import PRECISION_WHOLE, EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import LetPotConfigEntry, LetPotDeviceCoordinator
from .watering import async_update_watering
from .entity import LetPotEntity, LetPotEntityDescription, exception_handler

# Each change pushes a 'full' device status with the change. The library will cache
# pending changes to avoid overwriting, but try to avoid a lot of parallelism.
PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class LetPotNumberEntityDescription[_DataT: LetPotDeviceStatus](
    LetPotEntityDescription, NumberEntityDescription
):
    """Describes a LetPot number entity."""

    max_value_fn: Callable[[LetPotDeviceCoordinator[_DataT]], float]
    value_fn: Callable[[LetPotDeviceCoordinator[_DataT]], float | None]
    set_value_fn: Callable[[LetPotDeviceClient, str, float], Coroutine[Any, Any, None]]


NUMBERS: tuple[LetPotNumberEntityDescription[LetPotDeviceStatus], ...] = (
    LetPotNumberEntityDescription[LetPotDeviceStatus](
        key="light_brightness_levels",
        translation_key="light_brightness",
        value_fn=(
            lambda coordinator: (
                coordinator.device_client.get_light_brightness_levels(
                    coordinator.device.serial_number
                ).index(coordinator.data.light_brightness)
                + 1
                if isinstance(coordinator.data, LetPotGardenStatus) and coordinator.data.light_brightness is not None
                else None
            )
        ),
        set_value_fn=(
            lambda device_client, serial, value: device_client.set_light_brightness(
                serial,
                device_client.get_light_brightness_levels(serial)[int(value) - 1],
            )
        ),
        supported_fn=(
            lambda coordinator: (
                isinstance(coordinator.data, LetPotGardenStatus) and
                DeviceFeature.LIGHT_BRIGHTNESS_LEVELS
                in coordinator.device_client.device_info(
                    coordinator.device.serial_number
                ).features
            )
        ),
        native_min_value=float(1),
        max_value_fn=lambda coordinator: float(
            len(
                coordinator.device_client.get_light_brightness_levels(
                    coordinator.device.serial_number
                )
            )
        ),
        native_step=PRECISION_WHOLE,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
    ),
    LetPotNumberEntityDescription[LetPotDeviceStatus](
        key="plant_days",
        translation_key="plant_days",
        native_unit_of_measurement=UnitOfTime.DAYS,
        value_fn=lambda coordinator: coordinator.data.plant_days if isinstance(coordinator.data, LetPotGardenStatus) else None,
        set_value_fn=(
            lambda device_client, serial, value: device_client.set_plant_days(
                serial, int(value)
            )
        ),
        native_min_value=float(0),
        max_value_fn=lambda _: float(999),
        native_step=PRECISION_WHOLE,
        mode=NumberMode.BOX,
        supported_fn=lambda coordinator: isinstance(coordinator.data, LetPotGardenStatus),
    ),
    LetPotNumberEntityDescription[LetPotDeviceStatus](
        key="manual_duration",
        translation_key="manual_duration",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda coordinator: (
            coordinator.data.pump_manual_duration
            if isinstance(coordinator.data, LetPotWateringSystemStatus)
            else None
        ),
        set_value_fn=lambda device_client, serial, value: async_update_watering(
            device_client, serial, pump_manual_duration=int(value)
        ),
        native_min_value=float(0),
        max_value_fn=lambda _: float(65535),
        native_step=PRECISION_WHOLE,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        supported_fn=lambda coordinator: isinstance(coordinator.data, LetPotWateringSystemStatus),
    ),
    LetPotNumberEntityDescription[LetPotDeviceStatus](
        key="cycle_frequency",
        translation_key="cycle_frequency",
        native_unit_of_measurement=UnitOfTime.HOURS,
        value_fn=lambda coordinator: (
            coordinator.data.pump_cycle_frequency
            if isinstance(coordinator.data, LetPotWateringSystemStatus)
            else None
        ),
        set_value_fn=lambda device_client, serial, value: async_update_watering(
            device_client, serial, pump_cycle_frequency=int(value)
        ),
        native_min_value=float(0),
        max_value_fn=lambda _: float(65535),
        native_step=PRECISION_WHOLE,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        supported_fn=lambda coordinator: isinstance(coordinator.data, LetPotWateringSystemStatus),
    ),
    LetPotNumberEntityDescription[LetPotDeviceStatus](
        key="cycle_duration",
        translation_key="cycle_duration",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda coordinator: (
            coordinator.data.pump_cycle_duration
            if isinstance(coordinator.data, LetPotWateringSystemStatus)
            else None
        ),
        set_value_fn=lambda device_client, serial, value: async_update_watering(
            device_client, serial, pump_cycle_duration=int(value)
        ),
        native_min_value=float(0),
        max_value_fn=lambda _: float(65535),
        native_step=PRECISION_WHOLE,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        supported_fn=lambda coordinator: isinstance(coordinator.data, LetPotWateringSystemStatus),
    ),
    LetPotNumberEntityDescription[LetPotDeviceStatus](
        key="cycle_work_interval",
        translation_key="cycle_work_interval",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda coordinator: (
            coordinator.data.pump_cycle_workinginterval
            if isinstance(coordinator.data, LetPotWateringSystemStatus)
            else None
        ),
        set_value_fn=lambda device_client, serial, value: async_update_watering(
            device_client, serial, pump_cycle_workinginterval=int(value)
        ),
        native_min_value=float(0),
        max_value_fn=lambda _: float(65535),
        native_step=PRECISION_WHOLE,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        supported_fn=lambda coordinator: isinstance(coordinator.data, LetPotWateringSystemStatus),
    ),
    LetPotNumberEntityDescription[LetPotDeviceStatus](
        key="cycle_rest_interval",
        translation_key="cycle_rest_interval",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda coordinator: (
            coordinator.data.pump_cycle_restinterval
            if isinstance(coordinator.data, LetPotWateringSystemStatus)
            else None
        ),
        set_value_fn=lambda device_client, serial, value: async_update_watering(
            device_client, serial, pump_cycle_restinterval=int(value)
        ),
        native_min_value=float(0),
        max_value_fn=lambda _: float(65535),
        native_step=PRECISION_WHOLE,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        supported_fn=lambda coordinator: isinstance(coordinator.data, LetPotWateringSystemStatus),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LetPotConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up LetPot number entities."""
    coordinators = entry.runtime_data
    async_add_entities(
        LetPotNumberEntity[LetPotDeviceStatus](coordinator, description)
        for description in NUMBERS
        for coordinator in coordinators
        if description.supported_fn(coordinator)
    )


class LetPotNumberEntity[_DataT: LetPotDeviceStatus](
    LetPotEntity[_DataT], NumberEntity
):
    """Defines a LetPot number entity."""

    entity_description: LetPotNumberEntityDescription[_DataT]

    def __init__(
        self,
        coordinator: LetPotDeviceCoordinator[_DataT],
        description: LetPotNumberEntityDescription[_DataT],
    ) -> None:
        """Initialize LetPot number entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = (
            f"{coordinator.config_entry.unique_id}"
            f"_{coordinator.device.serial_number}"
            f"_{description.key}"
        )

    @property
    @override
    def native_max_value(self) -> float:
        """Return the maximum available value."""
        return self.entity_description.max_value_fn(self.coordinator)

    @property
    @override
    def native_value(self) -> float | None:
        """Return the number value."""
        return self.entity_description.value_fn(self.coordinator)

    @exception_handler
    @override
    async def async_set_native_value(self, value: float) -> None:
        """Change the number value."""
        return await self.entity_description.set_value_fn(
            self.coordinator.device_client,
            self.coordinator.device.serial_number,
            value,
        )
