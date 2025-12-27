"""Support for Roborock sensors with detailed debug logging."""

from __future__ import annotations

import datetime
import logging
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfArea, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .coordinator import (
    RoborockConfigEntry,
    RoborockDataUpdateCoordinator,
    RoborockDataUpdateCoordinatorA01,
    RoborockDataUpdateCoordinatorB01,
)
from .entity import (
    RoborockCoordinatedEntityA01,
    RoborockCoordinatedEntityB01,
    RoborockCoordinatedEntityV1,
    RoborockEntity,
)
from .models import DeviceState

_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class RoborockSensorDescription(SensorEntityDescription):
    value_fn: Callable[[DeviceState], StateType | datetime.datetime]
    is_dock_entity: bool = False


@dataclass(frozen=True, kw_only=True)
class RoborockSensorDescriptionA01(SensorEntityDescription):
    data_protocol: str


@dataclass(frozen=True, kw_only=True)
class RoborockSensorDescriptionB01(SensorEntityDescription):
    value_fn: Callable[[object], StateType]


def _dock_error_value_fn(state: DeviceState) -> str | None:
    if (
        status := state.status.dock_error_status
    ) is not None and state.status.dock_type != 0:  # RoborockDockTypeCode.no_dock
        return status.name
    return None


# ====================
# Generic V1 Sensors
# ====================
SENSOR_DESCRIPTIONS: list[RoborockSensorDescription] = [
    RoborockSensorDescription(
        key="battery",
        value_fn=lambda data: data.status.battery,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
    ),
    RoborockSensorDescription(
        key="cleaning_time",
        value_fn=lambda data: data.status.clean_time,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RoborockSensorDescription(
        key="dock_error",
        value_fn=_dock_error_value_fn,
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.ENUM,
        is_dock_entity=True,
    ),
]

# ====================
# A01 Sensors
# ====================
A01_SENSOR_DESCRIPTIONS: list[RoborockSensorDescriptionA01] = [
    RoborockSensorDescriptionA01(
        key="status",
        data_protocol="STATUS",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.ENUM,
    ),
    RoborockSensorDescriptionA01(
        key="battery",
        data_protocol="POWER",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
    ),
]

# ====================
# B01/Q7 Sensors
# ====================
Q7_B01_SENSOR_DESCRIPTIONS: list[RoborockSensorDescriptionB01] = [
    RoborockSensorDescriptionB01(
        key="q7_status",
        translation_key="q7_status",
        value_fn=lambda data: getattr(data, "status_name", None),
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.ENUM,
    ),
    RoborockSensorDescriptionB01(
        key="main_brush_time_left",
        translation_key="main_brush_time_left",
        value_fn=lambda data: getattr(data, "main_brush_time_left", None),
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RoborockSensorDescriptionB01(
        key="side_brush_time_left",
        translation_key="side_brush_time_left",
        value_fn=lambda data: getattr(data, "side_brush_time_left", None),
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RoborockSensorDescriptionB01(
        key="filter_time_left",
        translation_key="filter_time_left",
        value_fn=lambda data: getattr(data, "hypa_time_left", None),
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RoborockSensorDescriptionB01(
        key="sensor_time_left",
        translation_key="sensor_time_left",
        value_fn=lambda data: getattr(data, "main_sensor_time_left", None),
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RoborockSensorDescriptionB01(
        key="mop_life_time_left",
        translation_key="mop_life_time_left",
        value_fn=lambda data: getattr(data, "mop_life_time_left", None),
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RoborockSensorDescriptionB01(
        key="cleaning_time",
        translation_key="cleaning_time",
        value_fn=lambda data: getattr(data, "cleaning_time", None),
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RoborockSensorDescriptionB01(
        key="total_cleaning_time",
        translation_key="total_cleaning_time",
        value_fn=lambda data: getattr(data, "real_clean_time", None),
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RoborockSensorDescriptionB01(
        key="cleaning_area",
        translation_key="cleaning_area",
        value_fn=lambda data: getattr(data, "cleaning_area", None),
        native_unit_of_measurement=UnitOfArea.SQUARE_METERS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RoborockSensorDescriptionB01(
        key="total_cleaning_area",
        translation_key="total_cleaning_area",
        value_fn=lambda data: getattr(data, "total_cleaning_area", None),
        native_unit_of_measurement=UnitOfArea.SQUARE_METERS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
]


# ====================
# Setup Sensors
# ====================
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: RoborockConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Roborock sensors with debug logging."""
    coordinators = config_entry.runtime_data
    entities: list[RoborockEntity] = []

    _LOGGER.debug("Setting up Roborock V1 sensors")
    for coordinator in coordinators.v1:
        for description in SENSOR_DESCRIPTIONS:
            if description.value_fn(coordinator.data) is not None:
                _LOGGER.debug("Adding V1 sensor %s for device %s", description.key, coordinator.duid_slug)
                entities.append(RoborockSensorEntity(coordinator, description))

    _LOGGER.debug("Setting up Roborock A01 sensors")
    for coordinator in coordinators.a01:
        for description in A01_SENSOR_DESCRIPTIONS:
            if description.data_protocol in coordinator.request_protocols:
                _LOGGER.debug("Adding A01 sensor %s for device %s", description.key, coordinator.duid_slug)
                entities.append(RoborockSensorEntityA01(coordinator, description))

    _LOGGER.debug("Setting up Roborock B01/Q7 sensors")
    for coordinator in coordinators.b01:
        for description in Q7_B01_SENSOR_DESCRIPTIONS:
            if description.value_fn(coordinator.data) is not None:
                _LOGGER.debug("Adding B01 sensor %s for device %s", description.key, coordinator.duid_slug)
                entities.append(RoborockSensorEntityB01(coordinator, description))

    _LOGGER.debug("Adding %d sensors in total", len(entities))
    async_add_entities(entities)


# ====================
# Sensor Entity Classes
# ====================
class RoborockSensorEntity(RoborockCoordinatedEntityV1, SensorEntity):
    """Representation of a generic Roborock sensor."""

    entity_description: RoborockSensorDescription

    def __init__(self, coordinator: RoborockDataUpdateCoordinator, description: RoborockSensorDescription) -> None:
        self.entity_description = description
        _LOGGER.debug("Initializing V1 sensor entity %s", description.key)
        super().__init__(f"{description.key}_{coordinator.duid_slug}", coordinator, is_dock_entity=description.is_dock_entity)

    @property
    def native_value(self) -> StateType | datetime.datetime:
        value = self.entity_description.value_fn(self.coordinator.data)
        _LOGGER.debug("V1 sensor %s value: %s", self.entity_description.key, value)
        return value


class RoborockSensorEntityA01(RoborockCoordinatedEntityA01, SensorEntity):
    """Representation of an A01 Roborock sensor."""

    entity_description: RoborockSensorDescriptionA01

    def __init__(self, coordinator: RoborockDataUpdateCoordinatorA01, description: RoborockSensorDescriptionA01) -> None:
        self.entity_description = description
        _LOGGER.debug("Initializing A01 sensor entity %s", description.key)
        super().__init__(f"{description.key}_{coordinator.duid_slug}", coordinator)

    @property
    def native_value(self) -> StateType:
        value = self.coordinator.data[self.entity_description.data_protocol]
        _LOGGER.debug("A01 sensor %s value: %s", self.entity_description.key, value)
        return value


class RoborockSensorEntityB01(RoborockCoordinatedEntityB01, SensorEntity):
    """Representation of a B01/Q7 Roborock sensor."""

    entity_description: RoborockSensorDescriptionB01

    def __init__(self, coordinator: RoborockDataUpdateCoordinatorB01, description: RoborockSensorDescriptionB01) -> None:
        self.entity_description = description
        _LOGGER.debug("Initializing B01 sensor entity %s", description.key)
        super().__init__(f"{description.key}_{coordinator.duid_slug}", coordinator)

    @property
    def native_value(self) -> StateType:
        value = self.entity_description.value_fn(self.coordinator.data)
        _LOGGER.debug("B01 sensor %s value: %s", self.entity_description.key, value)
        return value
