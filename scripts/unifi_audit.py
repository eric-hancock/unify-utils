#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Eric Hancock
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation. This program is distributed without any
# warranty; see the LICENSE file for details.
"""Local, GET-only UniFi Network evidence collection. Python standard library only."""

import argparse
from datetime import datetime, timezone
import getpass
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import ssl
import sys
import time
import zipfile
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import urlopen

DEFAULT_STATE = Path(__file__).resolve().parents[1] / ".local"
SECRET_FIELD = re.compile(
    r"password|passphrase|preshared|privatekey|sharedsecret|secret|token|credential|radiuskey|^psk$|apikey",
    re.I,
)
BASE = "/proxy/network/integration"
COLLECTIONS = (
    "devices", "clients", "networks", "wifi/broadcasts", "firewall/zones",
    "firewall/policies", "acl-rules", "dns/policies", "traffic-matching-lists",
    "wans", "vpn/servers", "vpn/site-to-site-tunnels", "radius/profiles",
)
DETAILS = (
    ("devices", "deviceId"), ("clients", "clientId"),
    ("networks", "networkId"), ("wifi/broadcasts", "wifiBroadcastId"),
)
MAX_BYTES = 5_000_000
MAX_BUNDLE_BYTES = 50_000_000
PROJECT = Path(__file__).resolve().parents[1]


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def private_dir(path):
    if path.is_symlink():
        raise ValueError(f"Refusing symlink directory: {path}")
    path.mkdir(parents=True, mode=0o700, exist_ok=True)
    path.chmod(0o700)


def write_new(path, text):
    """Exclusive creation: never overwrite a credential, pin, or evidence file."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(text)


def write_json(path, value):
    write_new(path, json.dumps(value, indent=2) + "\n")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def scrub(value):
    if isinstance(value, dict):
        return {
            k: "REDACTED" if SECRET_FIELD.search(re.sub(r"[^a-zA-Z]", "", k)) else scrub(v)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [scrub(v) for v in value]
    return value


def validate_origin(origin):
    parsed = urlsplit(origin)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
        raise ValueError("Use an HTTPS origin only, e.g. https://192.168.1.1 (no credentials or path).")
    # Access .port to validate malformed port values before saving configuration.
    _ = parsed.port
    return origin.rstrip("/")


def validate_version(version):
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Network version must be numeric, e.g. 10.6.109.")
    return version


def tls_connection(origin):
    parsed = urlsplit(validate_origin(origin))
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE  # Replaced by exact pin verification before authentication.
    return http.client.HTTPSConnection(parsed.hostname, parsed.port or 443, context=context, timeout=15)


def certificate_hash(connection):
    return hashlib.sha256(connection.sock.getpeercert(binary_form=True)).hexdigest()


def load_key(path):
    if path.is_symlink():
        raise ValueError("Refusing a symlink key file.")
    key = path.read_text(encoding="utf-8").strip()
    if not key or any(char.isspace() for char in key):
        raise ValueError("Expected a nonempty saved key without whitespace.")
    return key


def initialize(state, origin, version):
    origin = validate_origin(origin)
    version = validate_version(version)
    private_dir(state)
    write_json(state / "config.json", {"console": origin, "network_version": version})
    print(f"Configuration saved in {state}. Next: trust, save-key, fetch-spec, check.")


def establish_trust(state, expected, tofu):
    if bool(expected) == bool(tofu):
        raise ValueError("Supply a nonempty expected fingerprint or explicitly select trust on first use.")
    config = read_json(state / "config.json")
    pin_path = state / "certificate.json"
    if pin_path.exists() or pin_path.is_symlink():
        raise ValueError("A certificate pin already exists; investigate certificate changes before replacing it.")
    if expected:
        expected = re.sub(r"[:\s]", "", expected).lower()
        if not re.fullmatch(r"[a-f0-9]{64}", expected):
            raise ValueError("Expected a 64-hex-character SHA-256 certificate fingerprint.")
    connection = tls_connection(config["console"])
    try:
        connection.connect()
        fingerprint = certificate_hash(connection)
        if expected and fingerprint != expected:
            raise ValueError("Certificate fingerprint does not match; no pin saved.")
        write_json(pin_path, {
            "origin": config["console"], "sha256": fingerprint, "observed_at": utc_now(),
            "trust": "trust on first use" if tofu else "user-supplied expected fingerprint",
        })
        print(f"Certificate SHA-256: {fingerprint}")
        print("Pinned without reading or sending the API key.")
        if tofu:
            print("Trust on first use does not independently verify the console's identity.")
    finally:
        connection.close()


def save_key(state):
    read_json(state / "config.json")
    destination = state / "api-key"
    if destination.exists() or destination.is_symlink():
        raise ValueError("Key file already exists; it was not changed.")
    if not sys.stdin.isatty():
        raise ValueError("Run save-key interactively in Terminal; keys must not be command arguments.")
    key = getpass.getpass("Paste UniFi API key (hidden), then press Return: ").strip()
    if not key or any(char.isspace() for char in key):
        raise ValueError("Expected a nonempty key without whitespace; nothing saved.")
    write_new(destination, key + "\n")
    print("Key saved privately; its value was not printed.")


def fetch_spec(state):
    config = read_json(state / "config.json")
    version = validate_version(config["network_version"])
    url = f"https://developer.ui.com/network/v{version}/openapi.json"
    # Public documentation only. This request never loads the local API key.
    with urlopen(url, timeout=30) as response:
        if urlsplit(response.url).hostname != "developer.ui.com":
            raise ValueError("Documentation redirected to an unexpected host.")
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("Specification exceeded the size limit.")
    spec = json.loads(raw)
    if not isinstance(spec.get("paths"), dict) or "/v1/sites" not in spec["paths"]:
        raise ValueError("Downloaded document is not the expected Network OpenAPI specification.")
    write_new(state / "openapi.json", json.dumps(spec, indent=2) + "\n")
    print(f"Saved public API specification for Network {version}.")


def build_handoff(state, collection, context_file=None):
    """Offline export: whitelist evidence JSON, never traverse the state directory."""
    collection = Path(collection)
    if collection.is_symlink() or not collection.is_dir():
        raise ValueError("Expected an existing, non-symlink collection directory.")
    manifest_path = collection / "manifest.json"
    if manifest_path.is_symlink() or manifest_path.stat().st_size > MAX_BYTES:
        raise ValueError("Invalid evidence manifest.")
    manifest = scrub(read_json(manifest_path))
    if not isinstance(manifest, dict) or manifest.get("status") not in (
            "completed", "completed_with_gaps", "interrupted"):
        raise ValueError("Expected a collector manifest with an explicit completion status.")
    files = sorted(p for p in collection.iterdir() if re.fullmatch(r"\d{3}\.json", p.name))
    if len(files) > 500 or manifest.get("requests") != len(files):
        raise ValueError("Evidence record count differs from the manifest; export stopped.")
    total_bytes = manifest_path.stat().st_size
    records = []
    for path in files:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
            raise ValueError("Invalid evidence record; export stopped.")
        total_bytes += path.stat().st_size
        if total_bytes > MAX_BUNDLE_BYTES:
            raise ValueError("Evidence exceeds the 50 MB handoff limit.")
        record = read_json(path)
        if not isinstance(record, dict) or record.get("method") != "GET":
            raise ValueError("Expected GET-only collector records.")
        records.append({**scrub(record), "evidence_file": path.name})
    context = (PROJECT / "examples/handoff-context.md").read_text(encoding="utf-8")
    if context_file:
        context_file = Path(context_file)
        if context_file.is_symlink() or context_file.stat().st_size > 100_000:
            raise ValueError("Context must be a non-symlink text file of at most 100 KB.")
        context = context_file.read_text(encoding="utf-8")
    parent = state / "handoffs"
    private_dir(parent)
    destination = parent / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    private_dir(destination)
    write_json(destination / "evidence.json", {
        "format": "unify-utils-handoff-v1", "exported_at": utc_now(),
        "manifest": manifest, "records": records,
    })
    write_new(destination / "CONTEXT.md", context)
    write_new(destination / "CODEX-PROMPT.md", (PROJECT / "examples/codex-analysis-prompt.md").read_text(encoding="utf-8"))
    write_new(destination / "report-template.md", (PROJECT / "examples/report-template.md").read_text(encoding="utf-8"))
    status = manifest["status"]
    write_new(destination / "HANDOFF.md", (
        "# Private UniFi analysis handoff\n\n"
        f"Collection status: **{status}**. Records: **{len(records)}**.\n\n"
        "This is collected evidence, not a completed assessment. Read the coverage gaps in "
        "evidence.json, especially if collection was interrupted. Missing data is not a healthy result.\n\n"
        "Review every file before sharing. Known credential fields are redacted, but IP/MAC addresses, "
        "SSIDs, names, topology, policy, and usage can remain. This bundle is not anonymous or encrypted.\n\n"
        "For local Codex, point the chat to this directory and use CODEX-PROMPT.md. "
        "For another environment, attach only this reviewed directory's files or its ZIP. "
        "Never attach the parent .local directory, API key, browser profile, or configuration backup.\n\n"
        "CONTEXT.md contains supplied context or a blank worksheet; the ZIP is a snapshot. "
        "If you edit a file after export, the ZIP does not update. Rebuild with --context to package revised context.\n"
    ))
    names = ("HANDOFF.md", "evidence.json", "CONTEXT.md", "CODEX-PROMPT.md", "report-template.md")
    write_json(destination / "checksums.json", {
        name: hashlib.sha256((destination / name).read_bytes()).hexdigest() for name in names
    })
    archive_path = destination / "codex-handoff.zip"
    fd = os.open(archive_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as output:
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name in (*names, "checksums.json"):
                entry = zipfile.ZipInfo(name)
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = 0o600 << 16
                archive.writestr(entry, (destination / name).read_bytes())
    print(f"Private handoff folder: {destination}")
    print(f"Optional upload archive: {archive_path}")
    print(f"Collection status: {status}. Review evidence and context before sharing with Codex.")
    return destination


class Collector:
    def __init__(self, state, site_id=None, budget=500, output=None):
        self.output = output
        self.state = state
        self.config = read_json(state / "config.json")
        validate_origin(self.config["console"])
        self.spec = read_json(state / "openapi.json")
        self.pin = read_json(state / "certificate.json")
        if self.pin["origin"] != self.config["console"]:
            raise ValueError("Pin belongs to a different console origin.")
        if not re.fullmatch(r"[a-f0-9]{64}", self.pin["sha256"]):
            raise ValueError("Invalid saved certificate fingerprint.")
        self.site_id = site_id
        self.budget = budget
        self.records = []
        self.gaps = []
        self.counts = {}
        self.started = utc_now()
        parent = state / "evidence"
        private_dir(parent)
        self.folder = parent / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        private_dir(self.folder)

    def get(self, template, values=None, query=None):
        if "get" not in self.spec["paths"].get(template, {}):
            self.gaps.append({"template": template, "reason": "GET not documented in selected specification"})
            return None
        path = template
        for name, value in (values or {}).items():
            encoded = quote(str(value), safe="")
            if encoded in (".", ".."):
                raise ValueError("Invalid path parameter.")
            path = path.replace("{" + name + "}", encoded)
        if "{" in path or not path.startswith("/v1/") or "?" in path:
            raise ValueError("Invalid or unresolved endpoint path.")
        if len(self.records) >= self.budget:
            raise ValueError("Request budget exhausted; partial evidence retained.")
        endpoint = BASE + path + ("?" + urlencode(query) if query else "")
        connection = tls_connection(self.config["console"])
        try:
            connection.connect()
            if certificate_hash(connection) != self.pin["sha256"]:
                raise ValueError("TLS certificate changed; stopped before reading or sending the key.")
            # Same TLS connection is checked and used; no redirect or reconnect with credentials.
            key = load_key(self.state / "api-key")
            observed = utc_now()
            connection.request("GET", endpoint, headers={"X-API-KEY": key, "Accept": "application/json"})
            response = connection.getresponse()
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("Response exceeded the size limit.")
            try:
                payload = scrub(json.loads(raw.decode("utf-8").replace(key, "REDACTED")))
            except (UnicodeDecodeError, json.JSONDecodeError):
                payload = {"non_json_response": True}  # Never store arbitrary HTML/error bodies.
            record = {"observed_at": observed, "method": "GET", "endpoint": endpoint,
                      "template": template, "http_status": response.status, "response": payload}
            self.records.append(record)
            write_json(self.folder / f"{len(self.records):03d}.json", record)
            print(f"{len(self.records):03d}: HTTP {response.status} {template}", flush=True, file=self.output)
            if response.status in (401, 429) or response.status >= 500:
                raise ValueError(f"Stopped on HTTP {response.status}; partial evidence retained.")
            if response.status != 200:
                self.gaps.append({"template": template, "status": response.status})
                if 300 <= response.status < 400:
                    raise ValueError("Redirect refused; credentials were not forwarded.")
                return None
            return payload
        finally:
            connection.close()
            time.sleep(0.15)

    def listing(self, template, values=None):
        items = []
        for _ in range(100):
            payload = self.get(template, values, {"offset": len(items), "limit": 200})
            if payload is None:
                return None  # A failure must never be represented as an empty configuration.
            data = payload.get("data")
            total = payload.get("totalCount")
            if (not isinstance(data, list) or not isinstance(total, int) or total < 0):
                raise ValueError("Unexpected pagination response; collection incomplete.")
            if not data and len(items) < total:
                raise ValueError("Pagination ended before totalCount; collection incomplete.")
            items.extend(data)
            if len(items) >= total:
                return items
        raise ValueError("Pagination limit exceeded.")

    def sites(self):
        info = self.get("/v1/info")
        if info is None or info.get("applicationVersion") != self.config["network_version"]:
            raise ValueError("Application version unavailable or differs from selected documentation; reinitialize after review.")
        sites = self.listing("/v1/sites")
        if sites is None:
            raise ValueError("Sites could not be read.")
        if self.site_id:
            sites = [s for s in sites if s["id"] == self.site_id]
        elif len(sites) > 1:
            raise ValueError("Multiple sites found: inspect the private sites response and rerun with --site-id.")
        if not sites:
            raise ValueError("No matching site available to this credential.")
        return sites

    def check(self):
        sites = self.sites()
        print(f"Authenticated successfully; selected sites: {len(sites)}")

    def collect(self):
        for site in self.sites():
            values = {"siteId": site["id"]}
            groups = {}
            for suffix in COLLECTIONS:
                template = "/v1/sites/{siteId}/" + suffix
                groups[suffix] = self.listing(template, values)
                self.counts[suffix] = None if groups[suffix] is None else len(groups[suffix])
            for suffix, param in DETAILS:
                for item in groups[suffix] or []:
                    detail_values = dict(values, **{param: item["id"]})
                    template = "/v1/sites/{siteId}/" + suffix + "/{" + param + "}"
                    self.get(template, detail_values)
                    if suffix == "devices":
                        self.get(template + "/statistics/latest", detail_values)
            for suffix in ("firewall/policies/ordering", "acl-rules/ordering"):
                self.get("/v1/sites/{siteId}/" + suffix, values)

    def telemetry(self, samples, interval):
        devices = []
        for site in self.sites():
            for device in self.listing("/v1/sites/{siteId}/devices", {"siteId": site["id"]}) or []:
                devices.append({"siteId": site["id"], "deviceId": device["id"]})
        if not devices:
            raise ValueError("No devices available for sampling; inspect coverage gaps.")
        for sample in range(samples):
            if sample:
                time.sleep(interval)
            for values in devices:
                self.get("/v1/sites/{siteId}/devices/{deviceId}/statistics/latest", values)

    def finish(self, status):
        write_json(self.folder / "manifest.json", {
            "started_at": self.started, "finished_at": utc_now(), "status": status,
            "console": self.config["console"], "network_version": self.config["network_version"],
            "documentation": f"https://developer.ui.com/network/v{self.config['network_version']}/openapi.json",
            "spec_sha256": hashlib.sha256((self.state / "openapi.json").read_bytes()).hexdigest(),
            "certificate_sha256": self.pin["sha256"], "tls_trust": self.pin["trust"],
            "requests": len(self.records), "methods": ["GET"], "counts": self.counts,
            "coverage_gaps": self.gaps,
        })
        print(f"Private evidence: {self.folder}", file=self.output)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE,
                        help="Private local state (default: repository .local directory)")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="Save console origin and installed Network version")
    init.add_argument("--console", required=True)
    init.add_argument("--network-version", required=True)
    trust = commands.add_parser("trust", help="Pin the public TLS certificate without sending credentials")
    choices = trust.add_mutually_exclusive_group(required=True)
    choices.add_argument("--fingerprint", help="Expected SHA-256 fingerprint verified independently")
    choices.add_argument("--trust-on-first-use", action="store_true", help="Explicitly trust the first certificate observed")
    commands.add_parser("save-key", help="Save the API key from a hidden interactive prompt")
    commands.add_parser("fetch-spec", help="Download the installed version's public OpenAPI spec")
    bundle = commands.add_parser("bundle", help="Package an existing collection offline; no key or network needed")
    bundle.add_argument("--collection", type=Path, required=True)
    bundle.add_argument("--context", type=Path, help="Optional context Markdown, copied verbatim; review before sharing")
    for name in ("check", "collect", "telemetry", "handoff"):
        command = commands.add_parser(name)
        command.add_argument("--site-id", help="Required when more than one site is available")
        command.add_argument("--max-requests", type=int, default=500, choices=range(1, 501), metavar="1..500")
        if name in ("telemetry", "handoff"):
            minimum = 0 if name == "handoff" else 1
            command.add_argument("--samples", type=int, default=3, choices=range(minimum, 11), metavar=f"{minimum}..10")
            command.add_argument("--interval", type=int, default=15, choices=range(15, 301), metavar="15..300")
        if name == "handoff":
            command.add_argument("--context", type=Path, help="Optional context Markdown, copied verbatim; review before sharing")
    args = parser.parse_args(argv)
    state = args.state_dir.absolute()
    try:
        if args.command == "init":
            initialize(state, args.console, args.network_version)
        elif args.command == "bundle":
            private_dir(state)
            build_handoff(state, args.collection, args.context)
        else:
            if not state.is_dir():
                raise ValueError("Run init first.")
            private_dir(state)
            if args.command == "trust":
                establish_trust(state, args.fingerprint, args.trust_on_first_use)
            elif args.command == "save-key":
                save_key(state)
            elif args.command == "fetch-spec":
                fetch_spec(state)
            else:
                collector = Collector(state, args.site_id, args.max_requests)
                status = "interrupted"
                try:
                    if args.command == "check":
                        collector.check()
                    elif args.command in ("collect", "handoff"):
                        collector.collect()
                        if args.command == "handoff" and args.samples:
                            collector.telemetry(args.samples, args.interval)
                    else:
                        collector.telemetry(args.samples, args.interval)
                    status = "completed_with_gaps" if collector.gaps else "completed"
                finally:
                    collector.finish(status)
                    if args.command == "handoff":
                        build_handoff(state, collector.folder, args.context)
    except (OSError, ValueError, KeyError, http.client.HTTPException, KeyboardInterrupt) as error:
        # Error strings from sockets/JSON are safe; never print HTTP response bodies or credentials.
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
