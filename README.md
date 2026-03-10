# SMS Gateway Integration for Home Assistant

This is a generic, fully customizable SMS Gateway integration for Home Assistant. It allows you to connect Home Assistant to almost any HTTP-based SMS gateway API to send text messages via the `notify` platform.

Because it is highly configurable directly from the UI, you can connect to simple REST APIs as well as more complex ones like the [SMS Gateway for Android™](https://github.com/capcom6/android-sms-gateway) application.

## Features

- **UI Configurable**: Set everything up directly from the Home Assistant integrations page.
- **GET & POST Support**: Works with simple URL parameter gateways or advanced JSON-based gateways.
- **Custom Headers**: Pass Authentication, API keys, and custom headers securely.
- **Custom Payload Templates**: Define a base JSON payload to be sent with every request.
- **Advanced Field Mapping**: Use dot-notation (e.g., `textMessage.text`) to dynamically inject the message or phone number deeply into nested JSON payloads. It automatically handles wrapping target phone numbers into arrays if the API requires it (e.g., `phoneNumbers`).
- **HACS Compatible**: Easy to install via the Home Assistant Community Store.

---

## Installation

### Method 1: HACS (Recommended)
1. Open HACS in your Home Assistant instance.
2. Click on the three dots in the top right corner and select **Custom repositories**.
3. Add the URL to this repository and select **Integration** as the category.
4. Click **Add**, then search for "SMS Gateway" in HACS and click **Download**.
5. Restart Home Assistant.

### Method 2: Manual
1. Download the `custom_components/sms_gateway` directory from this repository.
2. Place it in the `custom_components` directory of your Home Assistant configuration (e.g., `/config/custom_components/sms_gateway`).
3. Restart Home Assistant.

---

## Configuration

Once installed and your Home Assistant has restarted:
1. Go to **Settings** -> **Devices & Services** in Home Assistant.
2. Click **+ Add Integration** in the bottom right corner.
3. Search for **SMS Gateway**.
4. Fill out the configuration form based on your specific SMS Gateway API.

### Configuration Fields

- **Name**: A friendly name for this notification service.
- **URL**: The full HTTP/HTTPS URL of your SMS Gateway API endpoint.
- **Method**: Choose `POST` or `GET`.
- **Username** & **Password**: (Optional) For APIs that require Basic Authentication.
- **Headers**: A valid JSON string containing any extra HTTP headers required by the API (e.g., `{"Authorization": "Bearer YOUR_TOKEN"}`).
- **Payload Base**: A valid JSON string containing the static base structure of your request payload (e.g., `{"sender": "HomeAssistant"}`). Default is `{}`.
- **Target Key**: The JSON key where the recipient phone number should be injected. Use dot-notation for nested fields (e.g., `destination.phone`). If the API expects an array of numbers, the integration will automatically wrap the target(s) in a list and batch them into a single request if you name the key `phoneNumbers` or if the base payload already contains a list at that key. For all other target keys, sending to multiple targets will result in separate API requests being sent for each target.
- **Message Key**: The JSON key where the actual text message should be injected. Use dot-notation for nested fields (e.g., `textMessage.text`).
- **Default Target**: (Optional) The default phone number to send to if no target is provided in your automation.

---

## Examples

### Example 1: capcom6 / android-sms-gateway (Local Server)
The [android-sms-gateway](https://github.com/capcom6/android-sms-gateway) app turns an Android phone into an SMS Gateway. It expects a nested JSON structure and basic authentication.

**Configuration:**
- **URL**: `http://<device_local_ip>:8080/message`
- **Method**: `POST`
- **Username**: `your_username`
- **Password**: `your_password`
- **Headers**: `{}`
- **Payload Base**: `{"textMessage": {}}`
- **Target Key**: `phoneNumbers`
- **Message Key**: `textMessage.text`

*Note: Because you set `Target Key` to `phoneNumbers`, the integration will automatically format the request with an array. If you pass multiple targets in your automation, they will be batched into a single request like this:*
```json
{
  "textMessage": {
    "text": "Your Home Assistant Message"
  },
  "phoneNumbers": ["+15551234567", "+15557654321"]
}
```

### Example 2: Simple GET API
Some generic or older SMS gateways simply take query parameters via a GET request.

**Configuration:**
- **URL**: `https://api.smsprovider.com/send`
- **Method**: `GET`
- **Headers**: `{"X-Api-Key": "your-api-key-here"}`
- **Payload Base**: `{"from": "HA_Bot"}`
- **Target Key**: `to`
- **Message Key**: `msg`

*This will result in a request to: `https://api.smsprovider.com/send?from=HA_Bot&to=+15551234567&msg=Your+Home+Assistant+Message`*

### Example 3: Standard Flat POST API
A common, flat JSON REST API structure.

**Configuration:**
- **URL**: `https://api.smsprovider.com/v1/messages`
- **Method**: `POST`
- **Headers**: `{"Authorization": "Bearer YOUR_TOKEN"}`
- **Payload Base**: `{}`
- **Target Key**: `destination`
- **Message Key**: `body`

*This will result in the following JSON payload:*
```json
{
  "destination": "+15551234567",
  "body": "Your Home Assistant Message"
}
```

---

## Usage in Automations

Once configured, a notify service will be created (e.g., `notify.sms_gateway`). You can use it in your automations just like any other notification service.

```yaml
action:
  - service: notify.sms_gateway
    data:
      message: "The front door was opened!"
      target:
        - "+15551234567"
```
