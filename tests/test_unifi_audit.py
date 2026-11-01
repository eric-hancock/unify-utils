# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Eric Hancock
"""Offline checks of authentication boundaries, redaction, and collection gaps."""

import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock

SOURCE = Path(__file__).resolve().parents[1] / "scripts/unifi_audit.py"
MODULE = importlib.util.spec_from_file_location("unifi_audit", SOURCE)
audit = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(audit)

FAKE_CERT = b"synthetic public certificate for offline tests"
PIN = hashlib.sha256(FAKE_CERT).hexdigest()


class FakeResponse:
    def __init__(self, status=200, payload=None, raw=None):
        self.status = status
        self.raw = raw if raw is not None else json.dumps(payload or {}).encode()

    def read(self, size):
        return self.raw[:size]


class FakeConnection:
    def __init__(self, response=None, cert=FAKE_CERT):
        self.response = response or FakeResponse()
        self.cert = cert
        self.sock = self
        self.requests = []
        self.closed = False

    def connect(self):
        pass

    def getpeercert(self, binary_form=False):
        return self.cert

    def request(self, method, path, headers):
        self.requests.append((method, path, headers))

    def getresponse(self):
        return self.response

    def close(self):
        self.closed = True


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name) / "state"
        self.state.mkdir()
        self.key = "synthetic-test-key-not-a-real-credential"
        audit.write_json(self.state / "config.json", {
            "console": "https://192.0.2.1", "network_version": "10.6.109"})
        audit.write_json(self.state / "certificate.json", {
            "origin": "https://192.0.2.1", "sha256": PIN, "trust": "synthetic fixture"})
        audit.write_new(self.state / "api-key", self.key)
        audit.write_json(self.state / "openapi.json", {"paths": {
            "/v1/info": {"get": {}}, "/v1/sites": {"get": {}},
            "/v1/sites/{siteId}/networks": {"get": {}},
            "/v1/sites/{siteId}/devices/{deviceId}": {"get": {}},
        }})
        self.sleep = mock.patch.object(audit.time, "sleep")
        self.sleep.start()
        self.addCleanup(self.sleep.stop)

    def collector(self):
        return audit.Collector(self.state)

    def test_pin_mismatch_never_loads_or_sends_key(self):
        collector = self.collector()
        connection = FakeConnection(cert=b"different certificate")
        with mock.patch.object(audit, "tls_connection", return_value=connection), \
                mock.patch.object(audit, "load_key") as key_reader:
            with self.assertRaisesRegex(ValueError, "certificate changed"):
                collector.get("/v1/info")
        key_reader.assert_not_called()
        self.assertEqual(connection.requests, [])
        self.assertTrue(connection.closed)

    def test_get_redacts_nested_secrets_and_reflected_key_before_saving(self):
        collector = self.collector()
        connection = FakeConnection(FakeResponse(payload={
            "note": self.key, "securityConfiguration": {"passphrase": "private-value"},
            "nested": [{"radius_secret": "another-secret", "count": 2}],
        }))
        with mock.patch.object(audit, "tls_connection", return_value=connection):
            result = collector.get("/v1/info")
        self.assertEqual(connection.requests[0][0], "GET")
        self.assertEqual(connection.requests[0][2]["X-API-KEY"], self.key)
        self.assertEqual(result["nested"][0]["count"], 2)
        saved = (collector.folder / "001.json").read_text()
        for sensitive in (self.key, "private-value", "another-secret"):
            self.assertNotIn(sensitive, saved)
        self.assertEqual(result["securityConfiguration"]["passphrase"], "REDACTED")

    def test_redirect_is_not_followed(self):
        collector = self.collector()
        connection = FakeConnection(FakeResponse(status=302))
        with mock.patch.object(audit, "tls_connection", return_value=connection) as factory:
            with self.assertRaisesRegex(ValueError, "Redirect refused"):
                collector.get("/v1/info")
        self.assertEqual(factory.call_count, 1)
        self.assertEqual(len(connection.requests), 1)

    def test_undocumented_endpoint_never_connects(self):
        collector = self.collector()
        with mock.patch.object(audit, "tls_connection") as factory:
            self.assertIsNone(collector.get("/v1/not-documented"))
        factory.assert_not_called()
        self.assertEqual(len(collector.gaps), 1)

    def test_failed_list_is_gap_not_empty_success(self):
        collector = self.collector()
        connection = FakeConnection(FakeResponse(status=400, payload={
            "code": "synthetic-feature-unavailable"}))
        with mock.patch.object(audit, "tls_connection", return_value=connection):
            result = collector.listing("/v1/sites")
        self.assertIsNone(result)
        self.assertEqual(collector.gaps[0]["status"], 400)

    def test_pagination_reads_all_pages(self):
        collector = self.collector()
        with mock.patch.object(collector, "get", side_effect=[
            {"data": [{"id": "one"}, {"id": "two"}], "totalCount": 3},
            {"data": [{"id": "three"}], "totalCount": 3},
        ]) as get:
            self.assertEqual(len(collector.listing("/v1/sites")), 3)
        self.assertEqual(get.call_args_list[1].args[2]["offset"], 2)

    def test_pagination_rejects_truncated_response(self):
        collector = self.collector()
        with mock.patch.object(collector, "get", return_value={"data": [], "totalCount": 3}):
            with self.assertRaisesRegex(ValueError, "before totalCount"):
                collector.listing("/v1/sites")

    def test_version_mismatch_stops_before_site_collection(self):
        collector = self.collector()
        with mock.patch.object(collector, "get", return_value={"applicationVersion": "11.0.0"}), \
                mock.patch.object(collector, "listing") as listing:
            with self.assertRaisesRegex(ValueError, "differs"):
                collector.sites()
        listing.assert_not_called()

    def test_multisite_requires_selection(self):
        collector = self.collector()
        with mock.patch.object(collector, "get", return_value={"applicationVersion": "10.6.109"}), \
                mock.patch.object(collector, "listing", return_value=[{"id": "one"}, {"id": "two"}]):
            with self.assertRaisesRegex(ValueError, "Multiple sites"):
                collector.sites()
            collector.site_id = "two"
            self.assertEqual(collector.sites(), [{"id": "two"}])

    def test_non_json_body_is_not_saved(self):
        collector = self.collector()
        connection = FakeConnection(FakeResponse(raw=b"<html>private arbitrary response</html>"))
        with mock.patch.object(audit, "tls_connection", return_value=connection):
            collector.get("/v1/info")
        self.assertNotIn("private arbitrary response", (collector.folder / "001.json").read_text())

    def test_request_budget_stops_before_loading_key(self):
        collector = self.collector()
        collector.budget = 0
        with mock.patch.object(audit, "load_key") as key_reader:
            with self.assertRaisesRegex(ValueError, "budget"):
                collector.get("/v1/info")
        key_reader.assert_not_called()

    def test_manifest_preserves_partial_collection_and_gaps(self):
        collector = self.collector()
        collector.gaps.append({"template": "/v1/example", "status": 403})
        collector.counts["networks"] = None
        collector.finish("interrupted")
        manifest = audit.read_json(collector.folder / "manifest.json")
        self.assertEqual(manifest["status"], "interrupted")
        self.assertIsNone(manifest["counts"]["networks"])
        self.assertEqual(manifest["coverage_gaps"][0]["status"], 403)

    def test_private_file_refuses_overwrite(self):
        path = self.state / "api-key"
        with self.assertRaises(FileExistsError):
            audit.write_new(path, "replacement")
        self.assertEqual(path.read_text(), self.key)

    @unittest.skipIf(audit.os.name == "nt", "POSIX permission semantics")
    def test_evidence_has_private_permissions(self):
        collector = self.collector()
        collector.finish("completed")
        self.assertEqual(stat.S_IMODE(collector.folder.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((collector.folder / "manifest.json").stat().st_mode), 0o600)


class InputTests(unittest.TestCase):
    def test_origin_rejects_credentials_paths_and_plain_http(self):
        for origin in ("http://192.0.2.1", "https://user:password@192.0.2.1",
                       "https://192.0.2.1/path", "https://192.0.2.1?key=secret"):
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                audit.validate_origin(origin)

    def test_version_cannot_change_download_host_or_path(self):
        with self.assertRaises(ValueError):
            audit.validate_version("../../other-host")
        self.assertEqual(audit.validate_version("10.6.109"), "10.6.109")


if __name__ == "__main__":
    unittest.main()
