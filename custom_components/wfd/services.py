"""Home Assistant services for WFD."""

from typing import TYPE_CHECKING

from .errors import DuplicateMealError, InvalidMealNameError, MealNotFoundError, VoterNotFoundError, VoterUnavailableError
from .updates import async_signal_update

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

DOMAIN = "wfd"
ADD_MEAL, RENAME_MEAL, ARCHIVE_MEAL, RESTORE_MEAL = "add_meal", "rename_meal", "archive_meal", "restore_meal"
ADD_VOTER, ARCHIVE_VOTER, RESTORE_VOTER = "add_voter", "archive_voter", "restore_voter"
START_VOTING, SUBMIT_VOTE, CLOSE_VOTING = "start_voting", "submit_vote", "close_voting"


def _raise_service_error(exc: Exception) -> Exception:
    from homeassistant.exceptions import HomeAssistantError
    if isinstance(exc, (MealNotFoundError, DuplicateMealError, InvalidMealNameError, VoterNotFoundError, VoterUnavailableError)):
        return HomeAssistantError(str(exc))
    return exc


async def async_setup_services(hass: "HomeAssistant", meal_library, household, voting=None) -> None:
    """Register WFD services."""
    async def run(method, *args):
        try:
            await method(*args)
            async_signal_update(hass)
        except Exception as exc:
            raise _raise_service_error(exc) from exc

    async def add_meal(service_call):
        await run(meal_library.async_add_meal, service_call.data["name"])

    async def rename_meal(service_call):
        await run(meal_library.async_rename_meal, service_call.data["meal_id"], service_call.data["name"])

    async def archive_meal(service_call):
        await run(meal_library.async_archive_meal, service_call.data["meal_id"])

    async def restore_meal(service_call):
        await run(meal_library.async_restore_meal, service_call.data["meal_id"])

    async def add_voter(service_call):
        await run(household.async_add_voter, service_call.data["person_id"])

    async def archive_voter(service_call):
        await run(household.async_archive_voter, service_call.data["person_id"])

    async def restore_voter(service_call):
        await run(household.async_restore_voter, service_call.data["person_id"])

    for name, handler in ((ADD_MEAL, add_meal), (RENAME_MEAL, rename_meal), (ARCHIVE_MEAL, archive_meal), (RESTORE_MEAL, restore_meal), (ADD_VOTER, add_voter), (ARCHIVE_VOTER, archive_voter), (RESTORE_VOTER, restore_voter)):
        hass.services.async_register(DOMAIN, name, handler)

    if voting is None:
        return

    async def start_voting(service_call):
        await run(voting.async_create_round, service_call.data["meals_required"], service_call.data.get("deadline_minutes", 1440))

    async def submit_vote(service_call):
        await run(voting.async_submit_vote, service_call.data["round_id"], service_call.data["user_id"], service_call.data["meal_ids"])

    async def close_voting(service_call):
        await run(voting.async_close_round, service_call.data["round_id"])

    for name, handler in ((START_VOTING, start_voting), (SUBMIT_VOTE, submit_vote), (CLOSE_VOTING, close_voting)):
        hass.services.async_register(DOMAIN, name, handler)
