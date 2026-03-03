"""Config flow for SMS Gateway integration."""

from __future__ import annotations

import json
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant

from .const import (
    CONF_DEFAULT_TARGET,
    CONF_HEADERS,
    CONF_MESSAGE_KEY,
    CONF_METHOD,
    CONF_PAYLOAD,
    CONF_TARGET_KEY,
    CONF_URL,
    CONF_USERNAME,
    CONF_PASSWORD,
    DEFAULT_MESSAGE_KEY,
    DEFAULT_METHOD,
    DEFAULT_NAME,
    DEFAULT_TARGET_KEY,
    DOMAIN,
)


def validate_json(value: str | None) -> dict[str, Any] | None:
    """Validate and parse a JSON string."""
    if not value:
        return {}
    try:
        return json.loads(value)
    except ValueError:
        raise vol.Invalid("Invalid JSON string")


USER_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_URL): str,
        vol.Optional(CONF_METHOD, default=DEFAULT_METHOD): vol.In(["GET", "POST"]),
        vol.Optional(CONF_USERNAME): str,
        vol.Optional(CONF_PASSWORD): str,
        vol.Optional(CONF_HEADERS, default="{}"): str,
        vol.Optional(CONF_PAYLOAD, default="{}"): str,
        vol.Optional(CONF_TARGET_KEY, default=DEFAULT_TARGET_KEY): str,
        vol.Optional(CONF_MESSAGE_KEY, default=DEFAULT_MESSAGE_KEY): str,
        vol.Optional(CONF_DEFAULT_TARGET): str,
    }
)


class SmsGatewayConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SMS Gateway integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._async_abort_entries_match({CONF_NAME: user_input[CONF_NAME]})

            try:
                headers = validate_json(user_input.get(CONF_HEADERS, "{}"))
                payload = validate_json(user_input.get(CONF_PAYLOAD, "{}"))
            except vol.Invalid:
                errors["base"] = "invalid_json"
            else:
                user_input_cleaned = dict(user_input)
                user_input_cleaned[CONF_HEADERS] = headers
                user_input_cleaned[CONF_PAYLOAD] = payload

                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input_cleaned,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )
