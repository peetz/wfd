"""WFD update notifications."""

try:
    from homeassistant.helpers.dispatcher import async_dispatcher_send
except ModuleNotFoundError:
    def async_dispatcher_send(*args, **kwargs):
        """Test fallback when Home Assistant is unavailable."""
        return None


SIGNAL_WFD_UPDATED = "wfd_updated"


async def async_signal_update(hass) -> None:
    """Refresh registered entities before the service call returns."""
    async_dispatcher_send(hass, SIGNAL_WFD_UPDATED)
    entities = hass.data.get("wfd", {}).get("_entities", [])
    await __import__("asyncio").gather(
        *(entity._async_refresh() for entity in entities)
    )
