# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Eric Hancock
"""Offline checks of the MCP boundary; no console or real credentials required."""

import asyncio
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import unifi_mcp as adapter
from test_unifi_audit import FakeConnection, FakeResponse, PIN

audit = adapter.audit
SITE = "11111111-1111-4111-8111-111111111111"
DEVICE = "22222222-2222-4222-8222-222222222222"


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name)
        audit.write_json(self.state / "config.json", {
            "console": "https://192.0.2.1", "network_version": "10.6.109"})
        audit.write_json(self.state / "certificate.json", {
            "origin": "https://192.0.2.1", "sha256": PIN, "trust": "fixture"})
        audit.write_new(self.state / "api-key", "synthetic-key")
        audit.write_json(self.state / "openapi.json", {"paths": {
            path: {"get": {}} for path in ["/v1/info", "/v1/sites", "/v1/sites/{siteId}/networks"]}})
        self.reader = adapter.UnifiReader(self.state)
        self.connections = []
        self.responses = []

        def connection(_origin):
            conn = FakeConnection(FakeResponse(payload=self.responses.pop(0)))
            self.connections.append(conn)
            return conn

        self.patch = mock.patch.object(audit, "tls_connection", side_effect=connection)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.sleep = mock.patch.object(audit.time, "sleep")
        self.sleep.start()
        self.addCleanup(self.sleep.stop)

    def healthy(self, sites=None):
        self.responses.extend([
            {"applicationVersion": "10.6.109"},
            {"data": sites or [{"id": SITE}], "totalCount": len(sites) if sites else 1},
        ])

    def test_only_fixed_read_operations_and_uuid_parameters(self):
        for arguments in [dict(operation="delete"), dict(operation="list", resource="../../admin"),
                          dict(operation="detail", resource="devices", item_id="../x"),
                          dict(operation="status", site_id="https://evil.example")]:
            with self.assertRaises(ValueError):
                self.reader.run(**arguments)
        self.assertEqual(self.connections, [])

    def test_status_uses_get_only_and_does_not_print_on_stdout(self):
        self.healthy()
        with mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
            result = self.reader.run("status")
        self.assertEqual(result["status"], "complete")
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual([r[0] for c in self.connections for r in c.requests], ["GET", "GET"])
        self.assertTrue((Path(result["evidence_directory"]) / "manifest.json").exists())

    def test_redacts_credentials_before_mcp_output(self):
        self.healthy()
        self.responses.append({"data": [{"password": "private", "name": "synthetic-key"}], "totalCount": 1})
        result = self.reader.run("list", resource="networks")
        serialized = json.dumps(result)
        self.assertNotIn("private", json.dumps(result["data"]))
        self.assertNotIn("synthetic-key", serialized)

    def test_missing_endpoint_is_a_gap_not_empty_success(self):
        self.healthy()
        result = self.reader.run("list", resource="firewall/policies")
        self.assertEqual(result["status"], "coverage_gaps")
        self.assertIsNone(result["data"])
        self.assertEqual(len(self.connections), 2)

    def test_version_drift_stops_before_resource_requests(self):
        self.responses.append({"applicationVersion": "99.0.0"})
        result = self.reader.run("list", resource="networks")
        self.assertEqual(result["status"], "error")
        self.assertEqual(len(self.connections), 1)

    def test_site_discovery_allows_multiple_but_reads_require_selection(self):
        sites = [{"id": SITE}, {"id": DEVICE}]
        self.healthy(sites)
        self.assertEqual(len(self.reader.run("sites")["data"]), 2)
        self.healthy(sites)
        self.assertEqual(self.reader.run("status")["status"], "error")
        self.healthy(sites)
        self.assertEqual(self.reader.run("status", site_id=SITE)["status"], "complete")

    def test_exception_text_does_not_leak_to_mcp(self):
        with mock.patch.object(audit, "Collector", side_effect=ValueError("synthetic-secret")):
            self.assertNotIn("synthetic-secret", json.dumps(self.reader.run("status")))

    def test_statistics_reads_only_the_fixed_passive_endpoint(self):
        spec_path = self.state / "openapi.json"
        spec = audit.read_json(spec_path)
        spec["paths"]["/v1/sites/{siteId}/devices/{deviceId}/statistics/latest"] = {"get": {}}
        spec_path.write_text(json.dumps(spec))
        self.healthy()
        self.responses.append({"uptimeSec": 123})
        result = self.reader.run("statistics", item_id=DEVICE)
        self.assertEqual(result["data"]["uptimeSec"], 123)
        request = self.connections[-1].requests[0]
        self.assertEqual(request[:2], ("GET", f"/proxy/network/integration/v1/sites/{SITE}/devices/{DEVICE}/statistics/latest"))

    def test_large_output_is_explicitly_omitted_but_retained_in_evidence(self):
        self.healthy()
        self.responses.append({"data": [{"name": "large-record" * 100}], "totalCount": 1})
        with mock.patch.object(adapter, "MAX_RESULT_BYTES", 50):
            result = self.reader.run("list", resource="networks")
        self.assertTrue(result["data_omitted"])
        self.assertIsNone(result["data"])
        self.assertIn("large-record", (Path(result["evidence_directory"]) / "003.json").read_text())

    @unittest.skipUnless(importlib.util.find_spec("mcp"), "Optional MCP SDK not installed")
    def test_sdk_discovery_annotations_and_call(self):
        from mcp import Client

        async def exercise():
            server = adapter.build_server(self.state)
            async with Client(server) as client:
                result = await client.list_tools()
                self.assertEqual(len(result.tools), 5)
                self.assertTrue(all(tool.annotations.read_only_hint for tool in result.tools))
                self.assertFalse(any(tool.annotations.destructive_hint for tool in result.tools))
                response = await client.call_tool("unifi_list", {"resource": "../../admin"})
                self.assertTrue(response.is_error)
                self.healthy()
                response = await client.call_tool("unifi_status", {})
                self.assertFalse(response.is_error)
                self.assertIn("complete", str(response.structured_content))

        asyncio.run(exercise())


if __name__ == "__main__":
    unittest.main()
