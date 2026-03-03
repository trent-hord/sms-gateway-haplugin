"""The SMS Gateway component."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, discovery
from homeassistant.helpers.typing import ConfigType

from .const import DATA_HASS_CONFIG, DOMAIN, CONF_URL, CONF_METHOD, CONF_HEADERS, CONF_PAYLOAD, CONF_TARGET_KEY, CONF_MESSAGE_KEY, CONF_DEFAULT_TARGET, CONF_USERNAME, CONF_PASSWORD

PLATFORMS = [Platform.NOTIFY]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the SMS Gateway component."""
    hass.data[DATA_HASS_CONFIG] = config
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SMS Gateway from a config entry."""

    # remove unique_id for beta users
    if entry.unique_id is not None:
        hass.config_entries.async_update_entry(entry, unique_id=None)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data

    hass.async_create_task(
        discovery.async_load_platform(
            hass,
            Platform.NOTIFY,
            DOMAIN,
            {
                CONF_NAME: entry.data[CONF_NAME],
                CONF_URL: entry.data[CONF_URL],
                CONF_METHOD: entry.data[CONF_METHOD],
                CONF_USERNAME: entry.data.get(CONF_USERNAME),
                CONF_PASSWORD: entry.data.get(CONF_PASSWORD),
                CONF_HEADERS: entry.data.get(CONF_HEADERS, {}),
                CONF_PAYLOAD: entry.data.get(CONF_PAYLOAD, {}),
                CONF_TARGET_KEY: entry.data.get(CONF_TARGET_KEY),
                CONF_MESSAGE_KEY: entry.data.get(CONF_MESSAGE_KEY),
                CONF_DEFAULT_TARGET: entry.data.get(CONF_DEFAULT_TARGET),
                "entry_id": entry.entry_id,
            },
            hass.data[DATA_HASS_CONFIG],
        )
    )

    return True
