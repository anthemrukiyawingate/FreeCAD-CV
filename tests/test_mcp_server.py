"""Bounded MCP operation tests; SDK wire test runs when optional extra exists."""
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from cortexcad.mcp_server import curriculum_run, curriculum_preview, ping, create_server
from cortexcad.client import ExecutionResult


class MCPToolsTests(unittest.TestCase):
    def test_run_defaults_to_offline_preview(self):
        with patch("cortexcad.mcp_server.FreeCADClient") as client:
            result = curriculum_run("sketcher")
            client.assert_not_called()
        self.assertEqual(result["status"], "offline")
        self.assertFalse(result["success"])
        self.assertIn("recompute", result["script"])

    def test_live_is_explicit_and_unknown_outcome_is_preserved(self):
        with patch("cortexcad.mcp_server.FreeCADClient") as client:
            client.return_value.run_recipe.return_value = ExecutionResult(
                status="unknown", message="Inspect FreeCAD before retrying.")
            result = curriculum_run("sketcher", live=True)
            client.return_value.run_recipe.assert_called_once_with("sketcher", None)
        self.assertEqual(result["status"], "unknown")
        self.assertFalse(result["success"])

    def test_run_rejects_nonboolean_live_confirmation(self):
        for value in ("true", 1, 1.0, "false", 0, None):
            with self.subTest(value=value), patch("cortexcad.mcp_server.FreeCADClient") as client:
                with self.assertRaises(ValueError):
                    curriculum_run("sketcher", live=value)
                client.assert_not_called()

    def test_rejects_code_in_place_of_recipe(self):
        with patch("cortexcad.mcp_server.FreeCADClient") as client:
            with self.assertRaises(ValueError):
                curriculum_preview("import os; os.system('something')")
            client.assert_not_called()

    def test_ping_only_checks_bridge(self):
        with patch("cortexcad.mcp_server.FreeCADClient") as client:
            client.return_value.ping.return_value = ExecutionResult(status="ok", message="Bridge answered.")
            self.assertEqual(ping()["status"], "ok")
            client.return_value.ping.assert_called_once_with()
            client.return_value.run_recipe.assert_not_called()

    def test_missing_sdk_has_actionable_install_message(self):
        with patch.dict("sys.modules", {"mcp.server.fastmcp": None}):
            with self.assertRaisesRegex(RuntimeError, r"\[mcp\]"):
                create_server()

    def test_sdk_registers_only_bounded_tools(self):
        try:
            import mcp.server.fastmcp  # noqa: F401
        except ImportError:
            self.skipTest("Optional MCP SDK is not installed; tool-function contracts remain tested")
        import asyncio
        server = create_server()
        tools = asyncio.run(server.list_tools())
        self.assertEqual({tool.name for tool in tools}, {"ping", "curriculum_preview", "curriculum_run"})
        run = next(tool for tool in tools if tool.name == "curriculum_run")
        self.assertEqual(run.inputSchema["properties"]["live"]["default"], False)

    def test_sdk_does_not_coerce_boolean_dimensions(self):
        try:
            from mcp.server.fastmcp.exceptions import ToolError
        except ImportError:
            self.skipTest("Optional MCP SDK is not installed")
        import asyncio
        server = create_server()
        with self.assertRaises(ToolError):
            asyncio.run(server.call_tool("curriculum_preview", {"recipe": "sketcher", "parameters": {"length": True}}))

    def test_sdk_does_not_coerce_live_confirmation(self):
        try:
            from mcp.server.fastmcp.exceptions import ToolError
        except ImportError:
            self.skipTest("Optional MCP SDK is not installed")
        import asyncio
        server = create_server()
        for value in ("true", 1, 1.0, "false", 0, None):
            with self.subTest(value=value), patch("cortexcad.mcp_server.FreeCADClient") as client:
                client.return_value.run_recipe.return_value = ExecutionResult(status="ok", message="mock")
                with self.assertRaises(ToolError):
                    asyncio.run(server.call_tool("curriculum_run", {"recipe": "sketcher", "live": value}))
                client.assert_not_called()

    def test_stdio_handshake_preview_and_live_fake_bridge(self):
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError:
            self.skipTest("Optional MCP SDK is not installed")
        import asyncio
        from datetime import timedelta
        from test_client import rpc_server

        calls = []

        def execute(code):
            calls.append(code)
            return {"success": True, "message": "fake bridge acknowledged script"}

        async def session(endpoint, errlog):
            environment = {**os.environ, "CORTEXCAD_ENDPOINT": endpoint,
                           "CORTEXCAD_TIMEOUT": "1", "CORTEXCAD_TOKEN": ""}
            params = StdioServerParameters(command=sys.executable, args=["-m", "cortexcad.mcp_server"],
                                           cwd=str(Path(__file__).resolve().parents[1]), env=environment)
            async with stdio_client(params, errlog=errlog) as (read, write):
                async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=5)) as connection:
                    await connection.initialize()
                    tools = await connection.list_tools()
                    self.assertEqual({tool.name for tool in tools.tools}, {"ping", "curriculum_preview", "curriculum_run"})
                    health = await connection.call_tool("ping", {})
                    self.assertEqual(health.structuredContent["status"], "ok")
                    preview = await connection.call_tool("curriculum_run", {"recipe": "sketcher"})
                    self.assertEqual(preview.structuredContent["status"], "offline")
                    self.assertEqual(calls, [])
                    invalid = await connection.call_tool("curriculum_run", {"recipe": "arbitrary_python", "live": True})
                    self.assertTrue(invalid.isError)
                    self.assertEqual(calls, [])
                    live = await connection.call_tool("curriculum_run", {"recipe": "sketcher", "live": True})
                    self.assertEqual(live.structuredContent["status"], "ok")

        with rpc_server(execute) as (endpoint, _), tempfile.TemporaryFile(mode="w+") as errlog:
            asyncio.run(session(endpoint, errlog))
        self.assertEqual(len(calls), 1)
        self.assertIn("recompute", calls[0])


if __name__ == "__main__":
    unittest.main()
