# Chrome: the easier console inspection path

This workflow lets Codex read your signed-in UniFi pages, navigate settings, and extract tables directly. It avoids repeated screenshot pasting, particularly when the official API lacks a setting.

## 1. Connect the supported browser

OpenAI's [browser-extension documentation](https://learn.chatgpt.com/docs/chrome-extension) describes this setup. Availability and menu names depend on app rollout and workspace policy. It names the ChatGPT desktop settings and supports Work/Codex chats; do not assume every Codex app build has identical menus.

1. In the desktop app, look for **Settings → Computer Use**.
2. Select **Chrome** and follow the required browser-plugin setup.
3. Use **Install** to obtain the official extension through the app's store link.
4. Return to Computer Use and confirm Chrome shows **Manage** and is enabled.
5. In the same Chrome profile, open your console and sign in yourself. Use the local HTTPS origin if accessible, or your site's console through Site Manager.
6. In the chat, select **@Chrome**, or mention the console tab if available.
7. Approve access to the specific console site when prompted. A site approval and the browser's installation permissions are separate controls.

If the setting is absent, consult the current documentation for your app/workspace. Installing unrelated scraping extensions or enabling broad permissions is not a prerequisite for the API workflow.

The documented extension browsers include Chrome, Edge, Brave, Opera, and Vivaldi. Safari is not listed. A Safari login does not automatically become a Chrome login, and installing the extension does not by itself prove that the current chat has connected.

## 2. Give a precise read-only brief

```text
@Chrome Inspect my signed-in home UniFi console read-only.

Review WiFi/security settings, networks, existing firewall rules, port
forwarding, UPnP, WAN/LAN IPv6, threat protection, administrator roles,
and the available radio/client health metrics.

Do not change settings, submit configuration forms, create credentials,
install certificates, update firmware/engines, restart devices, migrate
the firewall, run RF scans, or start speed/load tests.

Keep secrets out of evidence. Document the exact paths that work for
my installed version. Distinguish configuration from tested behavior.
Save a Markdown report using this repository's report template.
```

The initial connection check should list available browser tabs and identify the intended UniFi site. If no signed-in console is available, sign in yourself. Passwords and MFA/recovery codes do not need to be placed in chat. Browser security warnings require your own review; the agent should hand control back rather than bypass them.

## 3. Read configuration through observed navigation

Use the [console map](console-map.md) as a starting point, verifying labels against the live page.

| Review | Evidence to record |
| --- | --- |
| Inventory | Model, OS/application/device versions, topology, uplink speed |
| Networks and SSIDs | VLAN assignments, isolation, authentication, PMF, enabled bands |
| Firewall | All IPv4/IPv6 categories, rule order, actions, state conditions, exceptions |
| Exposure | Port-forward count/details, active-WAN UPnP, VPN and remote management |
| IPv6 | WAN mode/address/prefix delegation and each LAN's interface type |
| Protection | Actual intrusion-prevention selection, not just subscription tier/signature count |
| Administration | Visible roles and access scope; mark MFA unknown if the page doesn't show it |
| WiFi health | Radio signal, interference, airtime, retries, band counts and client details |

Open existing detail panels to read their values, then close them. A page may open an empty creation form automatically; defaults there are **not applied policy**. Leave without submitting.

For controls whose text extraction lists both choices without marking a selection, inspect the screenshot or checked/selected accessibility state. Do not click an option just to discover its value. Virtualized tables may expose only rendered rows; capture appropriate views or use the official API before claiming completeness.

The agent should use the browser plugin's supplied client and instructions. A portable guide cannot prescribe its internal import paths: installed plugin versions and runtime APIs change. Do not copy runtime paths from someone else's machine or extract browser cookies to work around a failed connection.

## 4. Keep useful evidence and a readable walkthrough

For each observation, record date/time/timezone, installed versions, selected category/filter, page label, and the relevant selected values or table rows. Capture only what is needed. Store raw DOM snapshots/screenshots privately; account names, IPs, client names, and console identifiers can appear in them.

Write two documents locally:

- **Process guide:** actual clicks, icon locations, terminology, and recovery when menus differ.
- **Assessment report:** observed settings, supporting evidence references, implications, confidence, gaps, and recommended validation.

Use the [report template](../examples/report-template.md). Replace specific account/site identifiers before making anything public.

## 5. Troubleshooting

- **Mention accepted, but no browser access:** confirm Chrome is running, the extension is enabled in the same profile, and the app shows Manage. Reconnect/restart as described in the official documentation. The agent should use supplied plugin diagnostics rather than repairing native-host configuration itself.
- **Only a public search tool is available:** that tool cannot read your authenticated local console. Use the browser connection or the [API workflow](safari-api.md).
- **Login expired:** reauthenticate yourself; do not send session cookies to chat.
- **Unexpected account/site:** stop navigation and select the intended site.
- **Legacy firewall API fails:** read the existing UI rules; do not migrate firewall modes merely to expose an endpoint.

## Completion

Confirm no configuration changed, record anything untested, and leave the console on a useful inspected page. Remove browser site permission later if you no longer want it. Decide on configuration changes only after a concrete proposal with expected benefit, interruption, rollback, and retest.
