# Inspecting the console with Chrome

Use a connected browser for settings the API doesn't expose, such as legacy firewall rules. For repeated configuration and statistics reads, the [MCP server](mcp.md) avoids navigating the console each time.

## Connect the browser

Follow the official [browser-extension setup](https://learn.chatgpt.com/docs/chrome-extension) for your app. Availability and menu labels vary by app and workspace.

1. Look for **Settings → Computer Use → Chrome** and follow the extension setup.
2. Confirm the browser connection is enabled; the setup may show **Manage** once installed.
3. In the same Chrome profile, open your local console or Site Manager and sign in.
4. Select **@Chrome** in chat, if available, and approve access to the console site when prompted.

Ask Codex to list the available tabs and identify the intended UniFi site before inspecting it. A Safari login doesn't sign you into Chrome. If the browser connection isn't available, use the [local API workflow](safari-api.md).

Sign in and handle MFA yourself. Keep passwords, recovery codes, and session cookies out of chat. Review certificate warnings yourself before continuing.

## Start with a focused request

```text
@Chrome Inspect my signed-in home UniFi console read-only.

Check WiFi bands/security, SSID-to-network assignments, existing firewall
rules, port forwarding, UPnP, IPv6, and available radio/client statistics.
Use the repository's report template. Record the paths that work in my
installed version and flag anything you can't verify.

Do not save settings, create keys, update software, restart devices,
migrate the firewall, run RF scans, or start speed tests.
Keep credentials and account details out of saved evidence.
```

Add the actual problem: affected room, device, time of day, and what fails. The [console map](console-map.md) lists the paths used on the tested release.

## Read the saved settings

| Area | Useful details |
| --- | --- |
| Devices | Models, installed versions, topology, AP uplink speed |
| WiFi/networks | Bands, authentication, PMF, VLAN assignments, isolation |
| Firewall | IPv4/IPv6 categories, rule order, actions, state conditions, exceptions |
| Exposure | Port forwards, active-WAN UPnP, VPN, remote management |
| IPv6 | WAN mode/prefix delegation and each LAN's interface type |
| Protection/admin | Selected intrusion-prevention state and visible administrator roles |
| WiFi health | Client signal, retries, airtime, interference, band and AP |

Open existing detail panels and close them without saving. An empty creation form shows defaults, not an applied policy. If extracted text lists both choices, inspect the screenshot or selected state rather than clicking a control to find its value.

Tables may load only visible rows. Scroll through the list or use the API before treating it as a complete inventory. Mark MFA or other hidden settings unknown when the page doesn't show them.

## Save useful notes

Use the [report template](../examples/report-template.md). Record the date/time/timezone, installed versions, page path, selected filter, and relevant values. Keep screenshots and raw page captures private; see [privacy](privacy.md).

Separate what the console shows from what you've tested. A configured VLAN doesn't prove isolation works, and a good experience score doesn't establish coverage upstairs. Use the [assessment guide](assessment.md) for follow-up measurements.

## Troubleshooting

| Problem | Next step |
| --- | --- |
| Mention works but no browser access | Check the browser profile, extension, and app connection; reconnect using the official setup instructions |
| Only web search is available | Use the browser connection or local API; public search can't read your signed-in console |
| Login expired or wrong site | Sign in yourself or select the intended site before continuing |
| Legacy firewall API fails | Inspect existing rules in the UI; leave firewall migration alone |

Remove the browser's site permission when you no longer need it.
