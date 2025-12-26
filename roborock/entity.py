"""Support for Roborock device base class."""

from typing import Any
import logging

from roborock.data import Status
from roborock.devices.traits.v1.command import CommandTrait
from roborock.exceptions import RoborockException
from roborock.roborock_typing import RoborockCommand

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import (
    RoborockDataUpdateCoordinator,
    RoborockDataUpdateCoordinatorA01,
    RoborockDataUpdateCoordinatorB01,
)

_LOGGER = logging.getLogger(__name__)


class RoborockEntity(Entity):
    """Representation of a base Roborock Entity."""

    _attr_has_entity_name = True

    def __init__(self, unique_id: str, device_info: DeviceInfo) -> None:
        self._attr_unique_id = unique_id
        self._attr_device_info = device_info


class RoborockEntityV1(RoborockEntity):
    """Base class for Roborock V1 devices."""

    def __init__(self, unique_id: str, device_info: DeviceInfo, api: CommandTrait) -> None:
        super().__init__(unique_id, device_info)
        self._api = api

    async def send(self, command: RoborockCommand | str, params: dict[str, Any] | list[Any] | int | None = None) -> dict:
        try:
            response: dict = await self._api.send(command, params=params)
        except RoborockException as err:
            if isinstance(command, RoborockCommand):
                command_name = command.name
            else:
                command_name = command
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="command_failed",
                translation_placeholders={"command": command_name},
            ) from err
        return response


class RoborockCoordinatedEntityV1(RoborockEntityV1, CoordinatorEntity[RoborockDataUpdateCoordinator]):
    """Coordinated entity for V1 devices."""

    def __init__(self, unique_id: str, coordinator: RoborockDataUpdateCoordinator, is_dock_entity: bool = False) -> None:
        RoborockEntityV1.__init__(
            self,
            unique_id=unique_id,
            device_info=coordinator.device_info if not is_dock_entity else coordinator.dock_device_info,
            api=coordinator.properties_api.command,
        )
        CoordinatorEntity.__init__(self, coordinator=coordinator)
        self._attr_unique_id = unique_id

    @property
    def _device_status(self) -> Status:
        return self.coordinator.data.status

    async def send(self, command: RoborockCommand | str, params: dict[str, Any] | list[Any] | int | None = None) -> dict:
        res = await super().send(command, params)
        await self.coordinator.async_refresh()
        return res


class RoborockCoordinatedEntityA01(RoborockEntity, CoordinatorEntity[RoborockDataUpdateCoordinatorA01]):
    """Coordinated entity for A01 devices."""

    def __init__(self, unique_id: str, coordinator: RoborockDataUpdateCoordinatorA01) -> None:
        RoborockEntity.__init__(self, unique_id, device_info=coordinator.device_info)
        CoordinatorEntity.__init__(self, coordinator=coordinator)
        self._attr_unique_id = unique_id


class RoborockCoordinatedEntityB01(RoborockEntity, CoordinatorEntity[RoborockDataUpdateCoordinatorB01]):
    """Coordinated entity for B01/Q7 devices."""

    def __init__(self, unique_id: str, coordinator: RoborockDataUpdateCoordinatorB01) -> None:
        _LOGGER.debug("Initializing B01 coordinated entity %s", unique_id)
        RoborockEntity.__init__(self, unique_id, device_info=coordinator.device_info)
        CoordinatorEntity.__init__(self, coordinator=coordinator)
        self._attr_unique_id = unique_id
        self.coordinator = coordinator


class RoborockCoordinatedEntityV2(RoborockEntity):
    """Base entity for Roborock V2 devices."""

    def __init__(self, duid_slug: str, coordinator):
        self._duid_slug = duid_slug
        self._device = coordinator.device
        self._device_status = coordinator.device_status
        self.coordinator = coordinator
