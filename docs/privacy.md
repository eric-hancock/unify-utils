# Keeping network data private

## Local storage

The scripts keep the API key, console configuration, certificate pin, API spec, and evidence in `.local/`, which is ignored by Git. Files use mode 600 and directories use mode 700 on macOS/Linux. Windows ACL behavior hasn't been validated.

These files are plaintext. Your backups, sync tools, and other processes running as your user can still read them. If you choose a custom state directory, keep it outside published files or add it to the relevant ignore rules.

## What redaction leaves behind

The collector removes credential-like JSON fields, including passwords, tokens, private keys, and shared secrets. It also replaces exact API-key occurrences and discards non-JSON response bodies.

Evidence still contains IP/MAC addresses, SSIDs, names, UUIDs, topology, policy descriptions, and usage. Unexpected field names or encodings can also hide secrets the redactor misses. Review the files before sharing them.

The handoff ZIP excludes saved credentials and setup files, but isn't encrypted. Supplied context is copied verbatim. Browser screenshots can expose account details and form values; capture only the section you need. Keep configuration backups and support bundles private.

## Before committing or posting an issue

Publish code, generic instructions, templates, and fictional examples. Keep household reports and raw evidence local.

```sh
git status --short
git diff --cached --stat
git diff --cached
git ls-files .local .secrets private-evidence
```

The last command should print nothing. Review new files as well as diffs; untracked files don't appear in `git diff`. Ignoring a file doesn't remove it from Git history.

If you share a key accidentally, revoke it in UniFi immediately. Check repository history, remote copies, logs, and attachments for the leak as well.

## Access and cleanup

The collector and MCP server only make GET requests, but the key itself may permit writes elsewhere. A signed-in browser also retains your account's permissions. Use a dedicated key with a short expiry, keep MFA enabled, and keep console management off the public internet.

Revoke temporary keys when finished. Remove MCP registration or browser site access if no longer needed, and delete old evidence when you no longer need it.
