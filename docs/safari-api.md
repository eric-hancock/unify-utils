# Local API setup

Use a browser to set up the console connection, then Python to collect configuration and statistics. Safari works fine: the script uses its own API key and doesn't control the browser or read its cookies.

For guided setup and a bundle you can give Codex later, use [local handoff](local-handoff.md). For live reads from Codex, complete this setup and then install the [MCP server](mcp.md).

## 1. Find the console and installed version

Connect to your home LAN and open the console in your browser. Record:

- Console model or controller hosting type.
- Installed Network application version, not the UniFi OS, AP firmware, or phone app version.
- Local HTTPS origin, including the port if needed.

The [console map](console-map.md) shows where to find these. On macOS, **System Settings → Wi-Fi → Details → TCP/IP → Router** gives the gateway address. That is the console address only if the gateway hosts Network; a CloudKey or separate server has its own address.

The collector defaults to `/proxy/network/integration`, the UniFi OS API prefix. Other deployments may need a different base path and haven't been verified here. Traditional self-hosted Network commonly uses port 8443. Check the request format in your console rather than assuming the gateway address will work.

## 2. Initialize local state

Use Python 3.10 or newer; no pip packages are required. Run commands from the repository directory:

```sh
python3 scripts/unifi_audit.py init --console https://192.168.1.1 --network-version 10.6.109
```

Replace the address and version with yours. `10.6.109` is an example from the tested installation. The helper accepts numeric versions, not prerelease labels.

State goes in this clone's ignored `.local/` directory. `init` refuses to overwrite existing setup. For another console or version:

```sh
python3 scripts/unifi_audit.py --state-dir /private/path/another-audit init --console https://192.168.1.1 --network-version 10.6.109
```

Repeat `--state-dir` before each subsequent subcommand. Keep custom state directories private and out of Git.

## 3. Establish certificate trust

Local consoles often use self-signed certificates. The collector checks an exact SHA-256 certificate pin before loading or sending the API key; it doesn't change browser or system trust settings.

Check the certificate fingerprint independently, for example in the browser's certificate details after verifying the device and address, then run:

```sh
python3 scripts/unifi_audit.py trust --fingerprint VERIFIED_SHA256_FINGERPRINT
```

Use the certificate's SHA-256 fingerprint, not SHA-1 or a public-key pin. Colons and whitespace are accepted.

If you choose to trust the first certificate received instead:

```sh
python3 scripts/unifi_audit.py trust --trust-on-first-use
```

This fetches the certificate without credentials and pins it for later connections. It cannot detect an impostor present on that first connection. Use it only after deciding you trust the address and network.

A changed certificate stops later reads. Verify the cause before setting up a new state directory and pin; existing pins aren't overwritten.

## 4. Create and save an API key

1. Open **Network → Integrations**, the plug icon in the main toolbar on the tested release.
2. Check **Network API** and **API Request Format**. This helper expects `X-API-KEY` authentication and `/proxy/network/integration/v1/...` paths.
3. Choose **Create New API Key**, give it a name such as `home-audit`, and set an expiry long enough for your review.
4. Check the permissions your release offers. The tested 10.6.109 form had no read-only selector; the key may allow writes even though this collector only reads.
5. Save it through the hidden terminal prompt:

```sh
python3 scripts/unifi_audit.py save-key
```

Paste the key and press Return. The command requires an interactive terminal and refuses to overwrite a saved key. Keep the key out of command arguments, chat, and screenshots. Storage is private plaintext; see [privacy](privacy.md).

## 5. Download the matching API spec and check access

```sh
python3 scripts/unifi_audit.py fetch-spec
python3 scripts/unifi_audit.py check
```

`fetch-spec` downloads the installed version's public specification from `https://developer.ui.com/network/v<installed-version>/openapi.json`. It doesn't use the key or overwrite an existing spec.

`check` reads application information and sites, rejecting a version mismatch. If several sites are available, read the saved sites response and select the intended ID:

```sh
python3 scripts/unifi_audit.py check --site-id YOUR_SITE_ID
```

Use that `--site-id` on later collection commands too.

## 6. Collect

```sh
python3 scripts/unifi_audit.py collect
python3 scripts/unifi_audit.py telemetry --samples 3 --interval 15
```

`collect` reads configuration and current device statistics. `telemetry` takes passive samples; it doesn't run a speed test or RF scan.

Results go under `.local/evidence/<timestamp>/`. Response files record the request time, endpoint, HTTP status, and redacted JSON. `manifest.json` records the version, site, certificate/spec hashes, counts, gaps, and completion status.

List reads are paginated. Each command allows at most 500 requests by default; reduce that with `--max-requests`. Telemetry accepts 1–10 samples and intervals of 15–300 seconds. Authentication failures, rate limits, server errors, redirects, certificate changes, and version mismatches stop collection. Other unavailable endpoints are recorded as gaps; failed lists have a null count, not zero.

## 7. Fill gaps and review

Some settings require the console UI. In particular, **Zone Based Firewall is not configured** can mean the gateway uses legacy rules. Inspect those under **Settings → Policy Engine → Traffic & Firewall Rules → Advanced**. You don't need to migrate the firewall to collect evidence.

Use the [console map](console-map.md) for other UI checks, then the [assessment guide](assessment.md) and [report template](../examples/report-template.md) to work through the findings. Use [local handoff](local-handoff.md) to package the collection for Codex. Review identifiers before sharing and revoke the temporary key when finished.

## Troubleshooting

| Result | Next step |
| --- | --- |
| Can't reach the console | Check LAN/VLAN, HTTPS host/port, VPN routing, and local-network permissions |
| HTTP 401 | Check key expiry and access; revoke the old key before saving a replacement |
| HTTP 403 | Record the permission gap and check the account's intended access |
| HTTP 400: zone-based firewall not configured | Inspect legacy rules in the UI |
| HTTP 404 or missing GET in spec | Check installed version and hosting type; record unsupported endpoints |
| HTTP 429 or 5xx | Keep partial evidence and resolve the condition before retrying |
| Version mismatch | Review the upgrade and initialize a new state directory for that version |
| Changed certificate | Verify the console identity and reason for the change, then establish a new pin in fresh state |
| Partial collection | Read the manifest and failed responses before drawing conclusions |

Codex may ask for sandbox/network approval to reach the console or download the spec. Keep certificate verification enabled when resolving access problems.

References: [UniFi local management](https://help.ui.com/hc/en-us/articles/28457353760919-UniFi-Local-Management), [official API overview](https://help.ui.com/hc/en-us/articles/30076656117655-Getting-Started-with-the-Official-UniFi-API).
