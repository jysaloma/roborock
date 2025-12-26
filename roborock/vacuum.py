"""Roborock Vacuum integration for Home Assistant."""

import logging
from typing import Any
from homeassistant.components.vacuum import (
    StateVacuumEntity,
    VacuumEntityFeature,
    VacuumActivity,
)
from roborock.data.b01_q7.b01_q7_code_mappings import SCWindMapping, WaterLevelMapping
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import RoborockDataUpdateCoordinatorB01
from .entity import RoborockCoordinatedEntityB01

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Roborock vacuums for a config entry."""
    coordinators = config_entry.runtime_data
    _LOGGER.debug("Setting up Roborock vacuums for entry %s", config_entry.entry_id)

    entities = []

    for coordinator in coordinators.b01:
        device_name = coordinator.device_info["name"]
        _LOGGER.debug("Creating Roborock vacuum entity for device: %s", device_name)
        entity = RoborockVacuum(coordinator)
        entities.append(entity)

    async_add_entities(entities)
    _LOGGER.debug("Added %d Roborock vacuum(s)", len(entities))


class RoborockVacuum(RoborockCoordinatedEntityB01, StateVacuumEntity):
    """Representation of a Roborock B01/Q7 vacuum."""

    _attr_supported_features = (
        VacuumEntityFeature.START
        | VacuumEntityFeature.STOP
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.FAN_SPEED
    )

    def __init__(self, coordinator: RoborockDataUpdateCoordinatorB01):
        _LOGGER.debug("Initializing RoborockVacuum entity for %s", coordinator.device_info["name"])
        super().__init__(coordinator.device_info["name"], coordinator)
        self._available = True

    @property
    def name(self):
        return self.coordinator.device_info["name"]

    @property
    def activity(self) -> VacuumActivity | None:
        """Return the activity of the vacuum."""
        # B01Props has status_name directly, or we can check status code
        # Based on sensor.py: value_fn=lambda data: getattr(data, "status_name", None)
        status_name = getattr(self.coordinator.data, "status_name", None)
        
        if status_name == "cleaning":
            return VacuumActivity.CLEANING
        if status_name == "docked" or status_name == "charging":
            return VacuumActivity.DOCKED
        if status_name == "returning":
            return VacuumActivity.RETURNING
        if status_name == "error":
            return VacuumActivity.ERROR
        if status_name == "paused":
            return VacuumActivity.PAUSED
        return VacuumActivity.IDLE

    @property
    def fan_speed(self) -> str | None:
        """Return the fan speed of the vacuum cleaner."""
        # Map the internal code to a readable string if possible, or return the raw value
        # Assuming coordinator.data has a way to access current fan speed
        # Based on Q7PropertiesApi, we set it via SCWindMapping.
        # We need to find where the current value is stored in coordinator.data
        # For now, let's try to access it from status if available
        return getattr(self.coordinator.data, "fan_speed", None)

    @property
    def fan_speed_list(self) -> list[str]:
        """Return the list of available fan speeds."""
        return [mode.name for mode in SCWindMapping]

    async def async_set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        """Set fan speed."""
        try:
            mode = SCWindMapping[fan_speed]
            await self.coordinator.device.b01_q7_properties.set_fan_speed(mode)
        except KeyError:
            _LOGGER.error("Invalid fan speed: %s", fan_speed)

    async def async_start(self):
        _LOGGER.debug("Starting vacuum %s", self.name)
        await self.coordinator.device.b01_q7_properties.start_clean()

    async def async_stop(self):
        _LOGGER.debug("Stopping vacuum %s", self.name)
        await self.coordinator.device.b01_q7_properties.stop_clean()

    async def async_return_to_base(self):
        _LOGGER.debug("Returning vacuum %s to dock", self.name)
        await self.coordinator.device.b01_q7_properties.return_to_dock()
