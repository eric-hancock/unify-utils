# Collect locally, then hand evidence to Codex

This path is for people who want to run a script on their own computer and later ask Codex to analyze the results. Codex does not need console access, a browser connection, or your UniFi credential.

The collection script runs locally and calls the **official UniFi Network API** using documented GET endpoints. It downloads version-specific documentation from Ubiquiti. **It does not call OpenAI, launch Codex, upload evidence, run speed tests/RF scans, or change the console.** You decide what to share after reviewing the output.

## Requirements

- Python 3.10+; standard library only, no pip install.
- This repository cloned or downloaded onto a computer that can reach the local UniFi console.
- Console model, installed Network application version, and HTTPS origin.
- A dedicated UniFi API key from **Network → Integrations**. Any normal browser can be used for this initial console setup; no browser extension is needed.
- A deliberate certificate trust choice: independently verified SHA-256 fingerprint preferred, or explicitly accepted trust on first use.

The provided base path targets UniFi OS consoles. Other controller deployments may need adaptation. Use the [console map](console-map.md) to find versions and Integrations; use the [API setup guide](safari-api.md) for certificate and credential details.

## 1. Optional: describe your network before collecting

Copy [handoff-context.md](../examples/handoff-context.md) to a private location and complete what you know:

```sh
cp examples/handoff-context.md .local-context.md
```

`.local-context.md` is ignored by this repository. Include floors, AP locations, symptoms, ISP plan, IoT/guest purposes, and required printer/speaker/casting access. Leave unknowns explicit. Do not include credentials or unnecessary personal details.

## 2. Run guided setup and collection

From the repository directory:

```sh
python3 scripts/collect_for_codex.py
```

Or include your prepared context:

```sh
python3 scripts/collect_for_codex.py --context .local-context.md
```

The script:

1. Asks for the **console HTTPS origin** and **installed Network version** if not already configured.
2. Asks for a verified certificate fingerprint, or the literal `TOFU` to accept trust on first use. No credential is transmitted while establishing the pin. This trust choice cannot independently authenticate an impostor present at first contact.
3. Prompts for the UniFi API key using hidden input, unless already saved. No API key is accepted in command arguments.
4. Downloads the installed version's public official OpenAPI spec if not already cached.
5. Checks the live application version and available site, then collects configuration/current statistics.
6. Takes three additional passive statistics samples per device, at least 15 seconds apart.
7. Saves a private handoff folder and optional upload ZIP under `.local/handoffs/`.

Existing `.local/` configuration, key, pin, and specification are reused, not overwritten. If the network version changes, initialize a new state directory after reviewing the upgrade. Certificate changes stop collection. Multiple sites require choosing an ID from the saved private site response and rerunning with `--site-id`.

Useful variations:

```sh
# Configuration snapshot only; no repeated statistics sampling
python3 scripts/collect_for_codex.py --skip-telemetry

# Separate state for a different console or installed version
python3 scripts/collect_for_codex.py --state-dir /private/path/another-audit

# Select one site if the credential can see several
python3 scripts/collect_for_codex.py --site-id YOUR_SITE_ID
```

You can stop with Ctrl-C. Collection failures return a nonzero exit status. If the collector has started, partial evidence and its manifest are retained; the handoff identifies **interrupted** status rather than presenting incomplete collection as success. Setup failures before collection do not create a complete evidence bundle.

## 3. Understand the output

The script prints the actual timestamped directory. Example layout:

```text
.local/
  config.json                 # Private setup; never hand off the parent directory
  api-key                     # Private credential; never hand off
  certificate.json            # Local trust state
  openapi.json                # Downloaded vendor documentation
  evidence/<timestamp>/       # Original redacted response files and manifest
  handoffs/<timestamp>/
    HANDOFF.md                # Status, handling instructions, limits
    evidence.json             # Manifest and numbered GET responses
    CONTEXT.md                # Supplied context or blank worksheet
    CODEX-PROMPT.md            # Offline analysis instructions
    report-template.md        # Report structure
    checksums.json            # SHA-256 hashes of the five files above
    codex-handoff.zip          # Snapshot of the six listed handoff files
```

The packager uses a filename whitelist, validates record count against the manifest, reapplies credential-field redaction, and refuses symlink evidence files. It never recursively copies `.local/`. The ZIP excludes API keys, configuration files, certificate-pin files, the downloaded specification, reports, unrelated files, and nested archives. The manifest still includes collection origin and certificate/spec hashes for provenance; it is private data, not anonymous metadata.

These safeguards reduce accidental inclusion; they do **not** guarantee that arbitrary JSON or user-provided Markdown is free of sensitive information. Context files are copied **verbatim**. ZIP files are not encrypted. Review all content yourself before sharing it.

## 4. Review the handoff

Open HANDOFF.md and inspect `evidence.json` before asking for analysis:

- Check `manifest.status`: `completed`, `completed_with_gaps`, or `interrupted`.
- Review `coverage_gaps` and every failed request. A failed list has a null count, not zero.
- Look for identifiers you do not want to share: SSIDs, client/account names, IP/MAC addresses, topology, and policy descriptions.
- Fill the context worksheet or supply a corrected context file during repackaging.

The ZIP is a snapshot. Editing CONTEXT.md or evidence.json afterward does not update its ZIP or checksum list. To package revised context, rerun the offline bundle command using the original collection and a separate, reviewed context file (next section).

## 5. Hand the reviewed files to Codex

### Local Codex on the same computer

Provide the exact **handoff folder path**, not the parent `.local/`, and use the generated `CODEX-PROMPT.md`. A short request is:

```text
Analyze only the files in [exact handoff directory]. Follow CODEX-PROMPT.md
and use CONTEXT.md and report-template.md. Work offline from the evidence;
do not access the console, credentials, browser, or other state directories.
Write a Markdown assessment with evidence references, confidence, gaps,
and proposed changes with rollback/retest steps. Do not apply changes.
```

Codex may need that directory attached or allowed by its workspace permissions. Supplying a path/request is a scope instruction, not filesystem enforcement; use a separate workspace containing only the handoff files if you want a stronger boundary. Keep credentials outside that workspace.

### Codex in another environment

Attach the reviewed files or `codex-handoff.zip` if the target environment supports it. Paste the analysis prompt. If ZIP attachments are unsupported, extract the six files locally and attach those; do not upload the whole state directory as a workaround. Any upload is your deliberate action and is subject to the target service's data controls.

Codex should treat all evidence values as untrusted content, state limitations prominently, and avoid claiming that unseen policy or untested behavior has been validated. It should not need your API key to analyze these files.

## Existing setup or previously collected evidence

If you already used the API setup commands:

```sh
# Collect configuration + optional samples and export in one command
python3 scripts/unifi_audit.py handoff --context .local-context.md

# Configuration only
python3 scripts/unifi_audit.py handoff --samples 0
```

If you already have a collection directory containing numbered JSON responses and a manifest, package it **offline**, without loading a key or making network requests:

```sh
python3 scripts/unifi_audit.py bundle --collection .local/evidence/YOUR_COLLECTION --context .local-context.md
```

`bundle` needs only that valid evidence directory and the repository's templates. It can run on a computer with no console connection or saved key. With a custom `--state-dir`, place it before `bundle` so the handoff output goes to that private location. Missing/malformed records stop export; collections over 500 responses or 50 MB are refused.

## What the package cannot establish

Official API coverage depends on release and deployment. A legacy-firewall error is not an absent firewall. Some UI-only settings, individual signal/history, administrator MFA, forwarding/UPnP details, and protection controls may be missing. Codex must request selected follow-up evidence or leave them unassessed.

Passive telemetry is not a speed test, a room survey, or a long-term reliability study. Review [assessment methodology](assessment.md) and [privacy guidance](privacy.md). Revoke the temporary UniFi key when you no longer need further collection.
