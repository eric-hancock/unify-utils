# Collect locally, then analyze with Codex

Use this workflow to collect a snapshot on your own computer and give Codex the results later. The script reads the official UniFi Network API and builds a handoff folder. It doesn't upload anything, launch Codex, change settings, or run speed tests.

## What you need

- Python 3.10 or newer; no pip packages required.
- A copy of this repository on a computer that can reach the console over the LAN.
- The console HTTPS address, installed Network version, and a dedicated API key from **Network → Integrations**.
- The console's verified SHA-256 certificate fingerprint, or a decision to trust its certificate on first use.

Any browser works for console setup. The default API path targets UniFi OS consoles; other hosting types may need changes. See the [console map](console-map.md) and [API setup guide](safari-api.md) if you're unsure of the address, version, or certificate.

## 1. Add some context

This is optional, but helps explain what the statistics can't: where the APs are, which room has trouble, and what needs to keep working.

```sh
cp examples/handoff-context.md .local-context.md
```

Fill in what you know. `.local-context.md` is ignored by Git. Keep credentials out of it; the file is copied into the handoff verbatim.

## 2. Collect

From the repository directory, in an interactive terminal:

```sh
python3 scripts/collect_for_codex.py --context .local-context.md
```

Omit `--context` if you skipped the worksheet. The script asks for the address, installed Network version, certificate fingerprint, and API key. Key input is hidden. You can enter `TOFU` instead of a fingerprint to trust the first certificate received; that cannot detect an impostor on the first connection.

It then downloads the matching API specification, checks access, collects configuration/current statistics, and takes three additional passive statistics samples per device, at least 15 seconds apart. Existing setup is reused.

```sh
# Skip repeated statistics sampling
python3 scripts/collect_for_codex.py --skip-telemetry

# Use separate state for another console or installed version
python3 scripts/collect_for_codex.py --state-dir /private/path/another-audit

# Choose a site when the key can access several
python3 scripts/collect_for_codex.py --site-id YOUR_SITE_ID
```

For multiple sites, choose the ID from the saved sites response and rerun. After a Network upgrade or certificate change, follow the [API recovery instructions](safari-api.md#troubleshooting) before collecting again.

Ctrl-C stops collection. Failures return a nonzero exit status; evidence already collected is retained and marked `interrupted`. Setup failures may leave no handoff.

## 3. Review the output

The script prints the timestamped handoff path:

```text
.local/
  api-key                     # Credential; keep local
  config.json                 # Console setup
  certificate.json            # Certificate pin
  openapi.json                # Downloaded API spec
  evidence/<timestamp>/       # Original responses and manifest
  handoffs/<timestamp>/
    HANDOFF.md                # Collection status and handling notes
    evidence.json             # Manifest and numbered GET responses
    CONTEXT.md                # Your context or a blank worksheet
    CODEX-PROMPT.md            # Analysis instructions
    report-template.md
    checksums.json            # Hashes of the five files above
    codex-handoff.zip          # Those six files
```

Read `HANDOFF.md`, then check the manifest in `evidence.json`:

- `completed`: collection finished.
- `completed_with_gaps`: collection finished with unavailable endpoints.
- `interrupted`: collection stopped early.

Review failed requests and `coverage_gaps`. A failed list has a null count, not zero. Then check every file for names, SSIDs, IP/MAC addresses, and other details you don't want to share.

The package excludes the saved key, setup files, downloaded spec, and unrelated files. Credential fields are redacted, but the bundle still contains private network data and is not encrypted. See [privacy](privacy.md).

## 4. Give Codex the reviewed handoff

For Codex on the same computer, provide the exact handoff folder path and this request:

```text
Analyze only the files in [exact handoff directory]. Follow CODEX-PROMPT.md
and use CONTEXT.md and report-template.md. Work offline from the evidence.
Write a Markdown assessment with evidence references, gaps, and proposed
changes with rollback and retest steps. Do not apply changes or access
the console, credentials, browser, or other state directories.
```

If needed, attach or allow that folder in the workspace. A separate workspace containing only the handoff files gives a stronger boundary than a prompt alone.

For another environment, attach the reviewed ZIP or its six files, depending on attachment support. Use the generated prompt. Share the handoff folder, not the parent `.local/` directory.

## Reuse existing setup or evidence

With API setup already complete:

```sh
python3 scripts/unifi_audit.py handoff --context .local-context.md

# Configuration/current statistics without extra samples
python3 scripts/unifi_audit.py handoff --samples 0
```

To package an existing collection offline:

```sh
python3 scripts/unifi_audit.py bundle --collection .local/evidence/YOUR_COLLECTION --context .local-context.md
```

`bundle` needs no key or console connection. It validates the manifest and records, rejecting collections over 500 responses or 50 MB. For custom output storage, put `--state-dir /private/path` before `bundle`.

Editing exported files does not update their ZIP or checksums. To package revised context, run `bundle` again with the original collection and your updated context file.

## What to check next

The API may miss legacy firewall rules, some client details, and UI-only controls. Fill those gaps using the [console map](console-map.md). Passive samples also won't tell you whether a call works in the back bedroom; use the [assessment guide](assessment.md) for room tests and comparisons. Revoke the temporary key when you're done collecting.
