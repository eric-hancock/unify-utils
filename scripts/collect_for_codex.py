#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Eric Hancock
"""Interactive local setup, read-only collection, and offline Codex handoff export."""

import argparse
import http.client
from pathlib import Path
import sys

import unifi_audit as audit


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, default=audit.DEFAULT_STATE)
    parser.add_argument("--site-id")
    parser.add_argument("--context", type=Path, help="Your context Markdown; copied verbatim into the handoff")
    parser.add_argument("--skip-telemetry", action="store_true", help="Collect configuration without repeated statistics sampling")
    args = parser.parse_args(argv)
    if not sys.stdin.isatty():
        parser.error("Run this guided setup interactively in Terminal; use unifi_audit.py for separate commands.")
    state = args.state_dir.absolute()
    try:
        print("Local UniFi collection for later Codex analysis")
        print("Uses documented GET requests; no configuration changes, speed tests, scans, or model/API calls to OpenAI.")
        print("You need a local Network API key from UniFi Integrations. Keep it out of chat and command arguments.")
        if not (state / "config.json").exists():
            origin = input("Local console HTTPS origin (e.g. https://192.168.1.1): ").strip()
            version = input("Installed Network application version (e.g. 10.6.109): ").strip()
            audit.initialize(state, origin, version)
        else:
            audit.private_dir(state)
            config = audit.read_json(state / "config.json")
            print(f"Reusing configured Network version {config['network_version']}; state: {state}")
        if not (state / "certificate.json").exists():
            print("Verify the console identity. Prefer a certificate SHA-256 fingerprint checked independently.")
            fingerprint = input("Paste the SHA-256 fingerprint, or type TOFU to explicitly trust the first certificate: ").strip()
            audit.establish_trust(state, None if fingerprint == "TOFU" else fingerprint, fingerprint == "TOFU")
        if not (state / "api-key").exists():
            audit.save_key(state)
        if not (state / "openapi.json").exists():
            audit.fetch_spec(state)
        command = ["--state-dir", str(state), "handoff"]
        if args.site_id:
            command += ["--site-id", args.site_id]
        if args.context:
            command += ["--context", str(args.context)]
        if args.skip_telemetry:
            command += ["--samples", "0"]
        result = audit.main(command)
        print("Nothing was uploaded to Codex. Review the generated folder, complete context, then share it deliberately.")
        return result
    except (OSError, ValueError, KeyError, EOFError, http.client.HTTPException, KeyboardInterrupt) as error:
        print(f"Setup stopped: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
