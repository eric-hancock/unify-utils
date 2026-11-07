# Contributing

Useful contributions include verified menu paths for other UniFi releases, documented endpoint compatibility, clearer walkthroughs, and bounded read-only collection improvements.

Before proposing a change:

1. Run `python3 -m unittest discover -s tests -v`.
2. Use synthetic fixtures for tests. Do not commit real console responses or screenshots.
3. Keep console requests GET-only and credentials out of arguments, output, logs, and fixtures.
4. Preserve certificate checks before loading/transmitting credentials and refusal to follow authenticated redirects.
5. Preserve explicit coverage gaps and partial-collection status. Failed reads must not become empty successful configurations.
6. Include the deployment/model/software version for navigation claims and distinguish tested behavior from assumptions.
7. Review staged files with the [privacy checklist](docs/privacy.md).

For bugs, provide the command (without credentials), Python/platform/version information, HTTP status and sanitized error code, and whether collection stopped. Do not attach `.local/`, backups, session cookies, or API keys.

This project has no dependency installation step and no live-console tests in CI. An integration test against your own network is a separately authorized action; document what it actually validates.
