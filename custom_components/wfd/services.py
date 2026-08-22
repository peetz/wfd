"""Home Assistant services for WFD."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall
    from .meal_library import MealLibrary

from .errors import DuplicateMealError, InvalidMealNameError, MealNotFoundError

DOMAIN = "wfd"

ADD_MEAL = "add_meal"
RENAME_MEAL = "rename_meal"
ARCHIVE_MEAL = "archive_meal"
RESTORE_MEAL = "restore_meal"


def _raise_service_error(exc: Exception) -> Exception:
    from homeassistant.exceptions import HomeAssistantError

    if isinstance(exc, (MealNotFoundError, DuplicateMealError, InvalidMealNameError)):
        return HomeAssistantError(str(exc))
    return exc


async def async_setup_services(hass: "HomeAssistant", meal_library: "MealLibrary") -> None:
    """Register WFD meal management services."""

    async def add_meal(call: "ServiceCall") -> None:
        try:
            await meal_library.async_add_meal(call.data["name"])
        except Exception as exc:
            raise _raise_service_error(exc) from exc

    async def rename_meal(call: "ServiceCall") -> None:
        try:
            await meal_library.async_rename_meal(call.data["meal_id"], call.data["name"])
        except Exception as exc:
            raise _raise_service_error(exc) from exc

    async def archive_meal(call: "ServiceCall") -> None:
        try:
            await meal_library.async_archive_meal(call.data["meal_id"])
        except Exception as exc:
            raise _raise_service_error(exc) from exc

    async def restore_meal(call: "ServiceCall") -> None:
        try:
            await meal_library.async_restore_meal(call.data["meal_id"])
        except Exception as exc:
            raise _raise_service_error(exc) from exc

    hass.services.async_register(DOMAIN, ADD_MEAL, add_meal)
    hass.services.async_register(DOMAIN, RENAME_MEAL, rename_meal)
    hass.services.async_register(DOMAIN, ARCHIVE_MEAL, restore_meal)
    hass.services.async_register(DOMAIN, RESTORE_MEAL, restore_meal)
