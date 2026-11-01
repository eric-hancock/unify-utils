# Evidence, credentials, and publication

## Local files are private by default

The utility stores configuration, the API key, certificate pin, downloaded specification, and collected evidence in `.local/`. This directory is ignored by Git. Files created by the utility use mode 600; directories use mode 700. POSIX permissions provide the intended protection on macOS/Linux; Windows ACL behavior is not validated by this project.

These files are plaintext. Other processes running as your user, backups, cloud-sync tools, or administrators may still access them. `.gitignore` is not encryption and does not remove an already tracked file or a previously published secret.

## Redaction is limited

Before writing JSON, the collector removes values under credential-like keys such as password, passphrase, privateKey, token, and sharedSecret, and replaces exact API-key occurrences. It discards non-JSON response bodies.

This is **not an anonymizer or complete secret detector**. Output can still contain:

- Public/private IPs, MAC addresses, UUIDs, SSIDs, hostnames, and device/user names.
- DNS records, traffic lists, policy intent, topology, timestamps, and usage.
- Sensitive values stored under unexpected field names or encoded in unexpected forms.

Browser snapshots/screenshots can contain account names, emails, site identifiers, client activity, and unmasked form values. Avoid password/credential pages and collect only necessary fields. Configuration backups and support bundles need separate review; never attach them casually to a public issue.

## What belongs in the repository

Publish reusable source, generic instructions, blank templates, and clearly fictional examples. Do not publish a real household report or screenshots by default. Use generic host placeholders and relative paths; do not preserve someone else's certificate pin as a setup default.

Before a commit:

```sh
git status --short
git diff --cached --stat
git diff --cached
git ls-files .local .secrets private-evidence
```

The last command should show no generated private data. Also review filenames and newly added files; `git diff` alone does not show untracked files. If using a custom state directory, ensure it is outside your publication tree or ignored there too.

If a key is accidentally shared, revoke it in UniFi immediately. Removing a working-tree file is insufficient: evaluate Git history, remote copies, logs, and attachments separately. Do not post an active credential to demonstrate an error.

## Access boundaries

- The collector is GET-only; the credential itself may have write authority.
- A browser brief saying “read-only” does not remove administrator capabilities from the signed-in session.
- Certificate pinning requires a deliberate initial trust decision. First-use trust does not independently verify identity.
- Use scoped local access and short-lived credentials. Do not disable UI-account MFA or expose management to the internet for this workflow.
- Revoke temporary access when finished and keep evidence only as long as needed.
