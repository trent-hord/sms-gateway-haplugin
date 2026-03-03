"""Test the SMS Gateway notification service."""
import pytest
import requests_mock

from homeassistant.components.notify import ATTR_TARGET
from homeassistant.core import HomeAssistant

from custom_components.sms_gateway.const import (
    CONF_DEFAULT_TARGET,
    CONF_HEADERS,
    CONF_MESSAGE_KEY,
    CONF_METHOD,
    CONF_PAYLOAD,
    CONF_TARGET_KEY,
    CONF_URL,
    CONF_USERNAME,
    CONF_PASSWORD,
    DOMAIN,
)
from custom_components.sms_gateway.notify import SmsGatewayNotificationService


@pytest.fixture
def mock_hass():
    """Mock HomeAssistant instance."""
    class MockHass:
        data = {DOMAIN: {}}
    return MockHass()


def test_send_message_post(mock_hass, requests_mock):
    """Test sending a POST message via the SMS Gateway."""
    config = {
        CONF_URL: "http://example.com/api/sms",
        CONF_METHOD: "POST",
        CONF_HEADERS: {"Authorization": "Bearer secret_token"},
        CONF_PAYLOAD: {"sender": "HomeAssistant"},
        CONF_TARGET_KEY: "destination",
        CONF_MESSAGE_KEY: "body",
    }

    service = SmsGatewayNotificationService(mock_hass, config)

    # Mock the API endpoint
    requests_mock.post("http://example.com/api/sms", text="OK", status_code=200)

    # Send a message
    service.send_message("Hello from HA", **{ATTR_TARGET: ["+15551234567"]})

    # Verify the request
    assert requests_mock.called
    assert requests_mock.call_count == 1

    request = requests_mock.last_request
    assert request.method == "POST"
    assert request.headers["Authorization"] == "Bearer secret_token"
    assert request.json() == {
        "sender": "HomeAssistant",
        "destination": "+15551234567",
        "body": "Hello from HA"
    }


def test_send_message_get(mock_hass, requests_mock):
    """Test sending a GET message via the SMS Gateway."""
    config = {
        CONF_URL: "http://example.com/api/sms",
        CONF_METHOD: "GET",
        CONF_HEADERS: {"X-Api-Key": "my_api_key"},
        CONF_PAYLOAD: {"from": "HA_Bot"},
        CONF_TARGET_KEY: "to",
        CONF_MESSAGE_KEY: "msg",
    }

    service = SmsGatewayNotificationService(mock_hass, config)

    # Mock the API endpoint (query params are part of URL matching)
    import re
    requests_mock.get(re.compile("http://example.com/api/sms"), text="OK", status_code=200)

    # Send a message
    service.send_message("Testing GET", **{ATTR_TARGET: ["+15559876543"]})

    # Verify the request
    assert requests_mock.called
    assert requests_mock.call_count == 1

    request = requests_mock.last_request
    assert request.method == "GET"
    assert request.headers["X-Api-Key"] == "my_api_key"
    assert "from=HA_Bot" in request.url
    assert "to=%2B15559876543" in request.url
    assert "msg=Testing+GET" in request.url


def test_send_message_default_target(mock_hass, requests_mock):
    """Test sending a message with default target."""
    config = {
        CONF_URL: "http://example.com/api/sms",
        CONF_METHOD: "POST",
        CONF_TARGET_KEY: "number",
        CONF_MESSAGE_KEY: "text",
        CONF_DEFAULT_TARGET: "1112223333"
    }

    service = SmsGatewayNotificationService(mock_hass, config)

    requests_mock.post("http://example.com/api/sms", text="OK", status_code=200)

    # Send message WITHOUT explicit targets
    service.send_message("Default test")

    # Verify the request used default
    assert requests_mock.called
    request = requests_mock.last_request
    assert request.json() == {
        "number": "1112223333",
        "text": "Default test"
    }


def test_send_message_multiple_targets(mock_hass, requests_mock):
    """Test sending a message to multiple targets."""
    config = {
        CONF_URL: "http://example.com/api/sms",
        CONF_METHOD: "POST",
        CONF_TARGET_KEY: "number",
        CONF_MESSAGE_KEY: "text",
    }

    service = SmsGatewayNotificationService(mock_hass, config)
    requests_mock.post("http://example.com/api/sms", text="OK", status_code=200)

    # Send a message with multiple targets
    service.send_message("Multi target", **{ATTR_TARGET: ["+100", "+200"]})

    # Verify both requests were made
    assert requests_mock.call_count == 2

    request1 = requests_mock.request_history[0]
    assert request1.json() == {
        "number": "+100",
        "text": "Multi target"
    }

    request2 = requests_mock.request_history[1]
    assert request2.json() == {
        "number": "+200",
        "text": "Multi target"
    }


def test_send_message_nested_capcom6(mock_hass, requests_mock):
    """Test compatibility with capcom6/android-sms-gateway API."""
    config = {
        CONF_URL: "http://example.com/message",
        CONF_METHOD: "POST",
        CONF_HEADERS: {"Authorization": "Basic xxx"},
        CONF_PAYLOAD: {"textMessage": {}},
        CONF_TARGET_KEY: "phoneNumbers",
        CONF_MESSAGE_KEY: "textMessage.text",
    }

    service = SmsGatewayNotificationService(mock_hass, config)

    requests_mock.post("http://example.com/message", text="OK", status_code=202)

    service.send_message("Hello capcom6", **{ATTR_TARGET: ["+15551234567"]})

    assert requests_mock.called
    request = requests_mock.last_request

    expected_payload = {
        "textMessage": {
            "text": "Hello capcom6"
        },
        "phoneNumbers": ["+15551234567"]
    }
    assert request.json() == expected_payload


def test_send_message_basic_auth(mock_hass, requests_mock):
    """Test sending a message with basic authentication."""
    config = {
        CONF_URL: "http://example.com/api/sms",
        CONF_METHOD: "POST",
        CONF_USERNAME: "test_user",
        CONF_PASSWORD: "test_password",
        CONF_TARGET_KEY: "number",
        CONF_MESSAGE_KEY: "text",
    }

    service = SmsGatewayNotificationService(mock_hass, config)
    requests_mock.post("http://example.com/api/sms", text="OK", status_code=200)

    service.send_message("Auth test", **{ATTR_TARGET: ["+100"]})

    assert requests_mock.called
    request = requests_mock.last_request

    # requests library handles basic auth by adding the Authorization header automatically
    import base64
    auth_string = base64.b64encode(b"test_user:test_password").decode("utf-8")
    assert request.headers["Authorization"] == f"Basic {auth_string}"
    assert request.json() == {
        "number": "+100",
        "text": "Auth test"
    }
