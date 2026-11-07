#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Eric Hancock
"""Launch the server over stdio, discover tools, and optionally perform bounded live reads."""

import argparse
import asyncio
import json
from pathlib import Path
import sys

from mcp import Client, StdioServerParameters
from unifi_audit import DEFAULT_STATE


async def check(state, live, site_id):
    parameters = StdioServerParameters(command=sys.executable, args=[
        str(Path(__file__).with_name("unifi_mcp.py")), "--state-dir", str(state.resolve())])
    async with Client(parameters, read_timeout_seconds=180) as client:
        listing = await client.list_tools()
        print("Discovered tools: " + ", ".join(tool.name for tool in listing.tools))
        if not live:
            print("Discovery passed. No console requests made; add --live for GET-only checks.")
            return
        common = {"site_id": site_id} if site_id else {}
        for name, arguments in [
            ("unifi_status", common),
            ("unifi_list", dict(common, resource="devices")),
            ("unifi_list", dict(common, resource="networks")),
            ("unifi_list", dict(common, resource="wifi/broadcasts")),
        ]:
            result = await client.call_tool(name, arguments)
            if result.is_error:
                raise RuntimeError("MCP call failed; inspect server stderr.")
            payload = result.structured_content
            if payload is None:
                payload = json.loads(next(block.text for block in result.content if block.type == "text"))
            # Some hosts/SDKs wrap structured results under 'result'.
            if "status" not in payload and isinstance(payload.get("result"), dict):
                payload = payload["result"]
            data = payload.get("data")
            summary = {"tool": name, "resource": arguments.get("resource"),
                       "status": payload.get("status"),
                       "items": len(data) if isinstance(data, list) else None,
                       "requests": payload.get("requests"),
                       "evidence_directory": payload.get("evidence_directory")}
            print(json.dumps(summary))
            if payload.get("status") != "complete":
                raise RuntimeError("Live read incomplete. Inspect private evidence; do not treat it as empty configuration.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--live", action="store_true", help="Read status/devices/networks/WiFi from your console.")
    parser.add_argument("--site-id")
    args = parser.parse_args()
    asyncio.run(check(args.state_dir, args.live, args.site_id))
