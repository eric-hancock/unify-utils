# Safari + local scripting/API workflow

Use Safari for manual console setup and a Python utility for repeatable local API collection. **The script does not control Safari or reuse its cookies.** Its API key is a separate authentication mechanism. For signed-in page extraction without screenshots, use the [Chrome path](chrome.md).

## 1. Identify the installation

Connect the computer to the trusted home LAN. Find:

```text
Console model or controller hosting type:
Installed UniFi OS version (or N/A for traditional self-hosted Network):
Installed Network application version:
Local console HTTPS origin, including any nonstandard port:
Integrations / Network API documentation available:
```

Use the [console map](console-map.md). On macOS, **System Settings → Wi-Fi → Details → TCP/IP → Router** identifies your gateway. It identifies the console only when the gateway also hosts Network. A CloudKey or separate Network Server has its own address. Ethernet interfaces have their own network details.

Open the known console address in Safari and verify the expected device/site. Do not expose management ports on the internet. Traditional self-hosted Network commonly uses port 8443; the bundled collector's default `/proxy/network/integration` prefix targets UniFi OS consoles. Other deployments may need a different API base and are not claimed compatible without testing.

Ubiquiti documents local discovery/access in [UniFi Local Management](https://help.ui.com/hc/en-us/articles/28457353760919-UniFi-Local-Management).

## 2. Initialize local state

Install Python 3.10 or newer through a source you trust if it is not already available. No pip packages are needed. Clone this repository, change into its directory, and run:

```sh
python3 scripts/unifi_audit.py init --console https://192.168.1.1 --network-version 10.6.109
```

Replace both values. The version is the installed **Network** version, not UniFi OS or your phone app. Numeric version strings are required; prerelease version labels are not supported by this helper.

All state is saved under `.local/` next to the repository's scripts directory. It includes the console origin and is private even before keys/evidence are added. `init` refuses to overwrite existing configuration. For a separate console/version, use a new state directory:

```sh
python3 scripts/unifi_audit.py --state-dir /private/path/another-audit init --console https://192.168.1.1 --network-version 10.6.109
```

Repeat the same `--state-dir` before the subcommand for subsequent operations. Custom state directories are your responsibility to exclude from other repositories/backups/sharing.

## 3. Establish certificate trust

Many local consoles use a self-signed certificate. A vendor example may include `curl -k`, which disables ordinary certificate verification. This utility instead requires an exact SHA-256 certificate pin, checked **on the same connection before reading or sending the key**. It does not modify system/browser trust stores.

Preferred method: inspect the console's certificate fingerprint independently (for example, through the browser's certificate details after verifying the device/address), then supply that value:

```sh
python3 scripts/unifi_audit.py trust --fingerprint VERIFIED_SHA256_FINGERPRINT
```

Colons and whitespace in a SHA-256 fingerprint are accepted. Confirm that you are using the certificate fingerprint, not a SHA-1 digest or a public-key pin of another format. Comparing two requests on the same untrusted path is not independent identity verification.

Alternatively, explicitly bootstrap trust on first use:

```sh
python3 scripts/unifi_audit.py trust --trust-on-first-use
```

This retrieves and pins the public certificate **without credentials**. It protects against subsequent unexpected certificate changes, but cannot detect an impostor already present on the first connection. Make that choice deliberately on the intended local network.

If the certificate changes later, collection stops before loading/transmitting the key. Investigate whether the cause is certificate renewal, replacement/reset hardware, a wrong address, or another problem. Existing pins are not overwritten. After confirming the new identity, initialize a new state directory and establish trust again. Do not automate pin replacement or add a blanket insecure mode.

## 4. Create and save a dedicated API key

1. In Safari, open **Network → Integrations**. In the tested interface this is the plug icon in the far-left toolbar, **outside Settings**.
2. Open **Network API** to verify the documentation for your installed release.
3. Open **API Request Format** to verify the local origin, base prefix, and authentication header. This helper uses `X-API-KEY` and `/proxy/network/integration/v1/...`.
4. Choose **Create New API Key**. Use a descriptive name such as `home-audit` and a short expiry sufficient for your review.
5. Inspect whatever permissions/scopes your version offers. In the tested 10.6.109 form, only Name, Description, and Expiry were visible; there was no read-only selector. Do not call that credential read-only merely because this script is GET-only.
6. Create the key and save it through the hidden local prompt:

```sh
python3 scripts/unifi_audit.py save-key
```

Paste the key when prompted, then press Return. Do not place it in command arguments, chat, screenshots, or committed files. The helper requires an interactive terminal, refuses overwrite, and creates `.local/api-key` with permissions 600 inside a directory with permissions 700.

This is private plaintext storage, not encryption or isolation from other processes running as your user. Do not weaken your existing UI-account MFA; it is separate from API-key setup. See [Ubiquiti's API overview](https://help.ui.com/hc/en-us/articles/30076656117655-Getting-Started-with-the-Official-UniFi-API).

## 5. Fetch version-specific documentation and check access

```sh
python3 scripts/unifi_audit.py fetch-spec
python3 scripts/unifi_audit.py check
```

`fetch-spec` downloads the public official spec from `https://developer.ui.com/network/v<installed-version>/openapi.json`, without accessing the key. It refuses to overwrite an existing specification.

`check` requests application information and the site list. It rejects a different application version rather than silently assuming the selected documentation matches an upgraded controller. It saves timestamped private evidence even if a later check fails.

If several sites are available, `check` stops and asks for `--site-id`. Read the private sites response locally and select the intended site's ID:

```sh
python3 scripts/unifi_audit.py check --site-id YOUR_SITE_ID
```

No automatic all-site collection is performed.

## 6. Collect configuration and passive telemetry

```sh
python3 scripts/unifi_audit.py collect
python3 scripts/unifi_audit.py telemetry --samples 3 --interval 15
```

Use `--site-id` on each command when required. Outputs are timestamped subdirectories under `.local/evidence/`, with JSON files containing request time, method, endpoint, status, and sanitized response. `manifest.json` records specification hash, certificate pin/trust mode, selected version, counts, gaps, and whether collection completed or was interrupted.

The collector:

- Issues fixed, documented **GET** calls; no device/client actions, voucher reads, writes, scans, updates, or tests.
- Paginates list responses and rejects malformed or prematurely exhausted pages.
- Stops after at most 500 requests by default; reduce with `--max-requests` if desired.
- Uses a short delay between calls and bounded samples (1–10) / sample interval (15–300 seconds).
- Stops on authentication failure, rate limiting, server errors, redirects, certificate changes, or version mismatch.
- Records nonfatal HTTP errors and missing endpoints as coverage gaps. A failed list has count `null`, not zero.
- Redacts credential-like JSON keys and exact occurrences of the API key before saving. Non-JSON bodies are not saved.

These controls limit this utility's behavior; they do not constrain the underlying credential's permissions. Read [privacy limitations](privacy.md) before sharing output.

## 7. Fill API gaps using Safari

The official API may not expose all UI configuration or historical/client diagnostics. For each gap, record the corresponding page/table from Safari or provide a carefully selected export.

An important example: the firewall API can report **Zone Based Firewall is not configured** while the gateway has valid legacy firewall rules. Read **Settings → Policy Engine → Traffic & Firewall Rules → Advanced** and capture each IPv4/IPv6 category. Do not interpret this error as an absent firewall, and do not migrate modes just to collect evidence.

See the [console map](console-map.md) for UPnP, forwarding, IPv6, threat prevention, and radio metrics. Pair each screenshot with the selected tab/filter and timestamp. Avoid full support bundles and configuration backups unless their sensitivity and contents are understood.

## 8. Produce a report, then clean up

Ask Codex to read the private evidence and use the [report template](../examples/report-template.md). Require explicit unknowns for unavailable fields. A connected browser can supplement the API later without replacing it.

Revoke the audit key in UniFi when finished, stop any separately created test server, and decide how long to retain `.local/`. No background monitor is installed. Public reports require separate manual redaction of network/account identifiers.

## Troubleshooting

| Result | Next step |
| --- | --- |
| Cannot reach local address | Confirm trusted LAN/VLAN, host, HTTPS port, VPN routing, and any Codex network permission prompt |
| HTTP 401 | Check key expiry/site access; replace locally after revoking the old key |
| HTTP 403 | Record a permission gap; do not broaden access automatically |
| HTTP 400 with zone-based firewall not configured | Inspect existing legacy rules in the UI |
| HTTP 404 / missing GET in spec | Check installed version/deployment; mark unsupported coverage explicitly |
| HTTP 429 / 5xx | Stop, retain partial evidence, and retry only after resolving the condition |
| Version mismatch | Review the upgrade; initialize a fresh state directory for that installed version |
| Changed certificate | Independently verify identity before establishing a new pin |
| Partial collection | Inspect `manifest.json` and response statuses; never call missing data a healthy configuration |

Codex's shell/network sandbox may require approval for local console access or downloading documentation. Keep approvals scoped to the provided collector and destination; Full Access is not required by this guide.
