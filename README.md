# unify-utils

Practical tools and walkthroughs for reviewing a home **Ubiquiti UniFi** network with Codex: security configuration, WiFi reliability, and performance evidence.

Two workflows came out of a real console investigation. Both start with reading configuration; changes and active tests are separate decisions.

| Workflow | Best for | What you need |
| --- | --- | --- |
| **[Chrome: inspect the console directly](docs/chrome.md)** | Easiest setup; settings that the API doesn't expose | A supported Codex/ChatGPT desktop browser connection, official Chrome extension, and your signed-in console |
| **[Safari + local API collector](docs/safari-api.md)** | Structured, repeatable evidence without connecting a browser | Safari for manual console setup; Python 3.10+; a local Network API key and console network access |

The Safari workflow **does not automate or scrape Safari**. Python queries the local official API, and Safari supplies the settings/setup UI. Screenshots or selected exports fill API coverage gaps. Chrome can reduce that manual work by reading signed-in page content directly.

## Start here

1. Find your console model, installed UniFi OS and Network versions, and local console address. Use the **[console map](docs/console-map.md)**; menus vary by release.
2. Choose **[Chrome](docs/chrome.md)** or **[Safari/API](docs/safari-api.md)**. You can combine them.
3. Follow the **[assessment method](docs/assessment.md)** and use the **[report template](examples/report-template.md)** to separate observations, inferences, and untested behavior.
4. Read **[evidence privacy](docs/privacy.md)** before sharing output. Redacted evidence is still private network data.

## Local API quick start

The Python utility has **no third-party dependencies**. Run commands from the cloned repository. Substitute your actual console origin and **installed Network version**; `10.6.109` is the version used in the original investigation, not a claim about the latest release.

```sh
git clone https://github.com/eric-hancock/unify-utils.git
cd unify-utils
python3 scripts/unifi_audit.py init --console https://192.168.1.1 --network-version 10.6.109
```

Establish certificate trust **before sending a key**. Prefer an independently verified SHA-256 fingerprint:

```sh
python3 scripts/unifi_audit.py trust --fingerprint VERIFIED_SHA256_FINGERPRINT
```

Alternatively, explicitly accept trust on first use on your trusted local network:

```sh
python3 scripts/unifi_audit.py trust --trust-on-first-use
```

The first-use option cannot independently authenticate the router. These alternatives pin the exact certificate; later requests stop if it changes. See [certificate setup and recovery](docs/safari-api.md#3-establish-certificate-trust).

Create the key in **Network → Integrations**, then save it at a hidden prompt:

```sh
python3 scripts/unifi_audit.py save-key
python3 scripts/unifi_audit.py fetch-spec
python3 scripts/unifi_audit.py check
python3 scripts/unifi_audit.py collect
python3 scripts/unifi_audit.py telemetry --samples 3 --interval 15
```

`check` reads application info and sites. `collect` gathers documented configuration and current device statistics. `telemetry` takes bounded passive statistics samples; it does not run speed tests or RF scans. All authenticated API requests use **GET**, validate the certificate pin before loading the key, and remain on the configured local origin. No SSH access or inbound internet port is required.

## What's included

- Version-aware, paginated collection of devices, clients, networks, SSIDs, firewall zones/policies, ACLs, DNS policies, traffic lists, WAN and VPN overviews, and RADIUS profile overviews, where documented and available.
- Current device resource usage and radio retry statistics, where returned.
- Private timestamped evidence, coverage gaps, request metadata, and a reproducibility manifest.
- Known-working console navigation, including the Integrations plug icon and legacy firewall Simple/Advanced views.
- Example prompts, a report template, and a fictional example illustrating what conclusions the evidence can support.

Generated credentials, certificate pins, version-specific API specs, and evidence live under **`.local/`**, which is ignored by Git. The original household's audit report, addresses, device identifiers, certificates, and evidence are not included.

## Limits

- This is a configuration/evidence workflow, not a penetration test or guarantee of security.
- The key may permit writes even though the collector only issues GET requests. Inspect the actual permissions and revoke temporary access afterward.
- Missing/failed endpoints are recorded as gaps, not as empty configuration. Legacy firewall rules may require the console UI.
- Browser inspection is not an enforced read-only account. Keep the task scoped and avoid save/apply/create/update actions.
- Averages and client “experience” scores do not validate coverage in every room. Throughput, latency under load, and effective isolation require separately scoped measurements.

## Verification and contributions

```sh
python3 -m unittest discover -s tests -v
python3 scripts/unifi_audit.py --help
```

Tests run offline using synthetic data and mocked connections. They do not contact your console. The predecessor workflow was exercised on a **UCG Max, UniFi OS 5.1.34, Network 10.6.109, and U7 Pro Max**; the generalized utility is validated offline. Other versions/deployments may expose different endpoints and controls.

An optional [GitHub Actions template](examples/offline-tests-workflow.yml) runs those checks across Python 3.10, 3.12, and 3.14. It is provided as an example, not installed as an active workflow. A repository maintainer can copy it to `.github/workflows/tests.yml` with credentials permitted to manage workflows.

When reporting problems, include your model/software versions and sanitized status/error codes. Do not attach API keys, raw evidence directories, backup files, or browser sessions. See [CONTRIBUTING.md](CONTRIBUTING.md).

This is an independent project, not an official Ubiquiti or OpenAI product.

## License

Copyright © 2026 Eric Hancock. The original scripts, documentation, templates, tests, and workflow files in this repository are licensed under **GNU GPL version 3 only**, SPDX identifier **GPL-3.0-only**. See [LICENSE](LICENSE).

The downloaded Ubiquiti API specification is not bundled or relicensed by this project. Linked vendor documentation, browser extensions, and other third-party products retain their own terms. The software is provided without warranty; see the license for the full terms.
