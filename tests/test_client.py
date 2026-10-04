"""Failure-first IPC contracts: real loopback servers, no FreeCAD substitute."""
from __future__ import annotations

import contextlib
import io
import json
import os
import socket
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from xmlrpc.client import Fault
from xmlrpc.server import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer

from cortexcad.client import FreeCADClient, preview_recipe
from cortexcad.__main__ import main


@contextlib.contextmanager
def rpc_server(execute=None, ping=None):
    headers = []

    class Handler(SimpleXMLRPCRequestHandler):
        def do_POST(self):
            headers.append(self.headers.get("Authorization"))
            super().do_POST()

    server = SimpleXMLRPCServer(("127.0.0.1", 0), requestHandler=Handler,
                                allow_none=True, logRequests=False)
    server.register_function(ping or (lambda: True), "ping")
    server.register_function(execute or (lambda code: {"success": True, "message": "done"}),
                             "execute_code")
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", headers
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@contextlib.contextmanager
def broken_http(mode):
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            calls.append(self.rfile.read(int(self.headers["Content-Length"])))
            if mode == "disconnect":
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
                return
            body = b"not XML"
            self.send_response(200 if mode == "malformed" else 503)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class ConfigurationTests(unittest.TestCase):
    def test_defaults_and_environment(self):
        with patch.dict(os.environ, {}, clear=True):
            client = FreeCADClient()
            self.assertEqual(client.endpoint, "http://127.0.0.1:9875")
            self.assertEqual(client.timeout, 5.0)
        with patch.dict(os.environ, {"CORTEXCAD_ENDPOINT": "http://127.0.0.1:19875",
                                     "CORTEXCAD_TIMEOUT": "0.25"}):
            self.assertEqual(FreeCADClient().timeout, 0.25)
            self.assertEqual(FreeCADClient().endpoint, "http://127.0.0.1:19875")

    def test_reject_nonfinite_nonpositive_and_boolean_timeout(self):
        for value in (0, -1, float("nan"), float("inf"), True, False, "nan", "bad", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                FreeCADClient(timeout=value)

    def test_reject_unsafe_or_invalid_endpoint_without_echoing_secrets(self):
        for url in ("ftp://127.0.0.1", "http://user:secret@127.0.0.1", "http://127.0.0.1/?token=secret",
                    "http://127.0.0.1/#secret", "http://", "http://127.0.0.1:0", ""):
            with self.subTest(url=url), self.assertRaises(ValueError) as caught:
                FreeCADClient(endpoint=url)
            self.assertNotIn("secret", str(caught.exception))

    def test_auth_header_and_log_redaction(self):
        with rpc_server() as (endpoint, headers), patch.dict(os.environ, {"CORTEXCAD_TOKEN": "private-token"}):
            with self.assertLogs("cortexcad.ipc", level="INFO") as logged:
                result = FreeCADClient(endpoint).execute("payload_secret = 9")
        self.assertTrue(result.success)
        self.assertEqual(headers, ["Bearer private-token"])
        raw = "\n".join(logged.output)
        self.assertNotIn("private-token", raw)
        self.assertNotIn("payload_secret", raw)
        event = json.loads(logged.records[-1].getMessage())
        self.assertEqual(event["status"], "ok")
        self.assertEqual(event["attempts"], 1)
        self.assertIn("request_id", event)


class TransportTests(unittest.TestCase):
    def test_ping_accepts_upstream_true_and_returns_serializable_result(self):
        with rpc_server() as (endpoint, _):
            result = FreeCADClient(endpoint).ping()
        self.assertTrue(result.success)
        self.assertEqual(result.status, "ok")
        json.dumps(result.to_dict(), allow_nan=False)

    def test_ping_rejects_truthy_nonboolean(self):
        for response in (1, "pong", {"success": True}, False):
            with self.subTest(response=response), rpc_server(ping=lambda: response) as (endpoint, _):
                self.assertEqual(FreeCADClient(endpoint).ping().status, "error")

    def test_execute_uses_single_upstream_argument(self):
        calls = []

        def execute(code):
            calls.append(code)
            return {"success": True, "message": "Output: verified"}

        with rpc_server(execute) as (endpoint, _):
            result = FreeCADClient(endpoint).execute("print('verified')")
        self.assertEqual(calls, ["print('verified')"])
        self.assertEqual(result.data["message"], "Output: verified")
        self.assertTrue(result.success)

    def test_known_script_failure_is_not_success(self):
        with rpc_server(lambda code: {"success": False, "error": "invalid shape"}) as (endpoint, _):
            result = FreeCADClient(endpoint).execute("raise ValueError()")
        self.assertEqual(result.status, "error")
        self.assertIn("partial", result.message.lower())

    def test_remote_gui_timeout_is_unknown(self):
        with rpc_server(lambda code: {"success": False, "code": "GUI_DISPATCH_STUCK", "error": "still running"}) as (endpoint, _):
            result = FreeCADClient(endpoint).execute("pass")
        self.assertEqual(result.status, "unknown")

    def test_legacy_remote_timeout_is_unknown(self):
        with rpc_server(lambda code: {"success": False, "error": "GUI dispatch timed out after 60s"}) as (endpoint, _):
            self.assertEqual(FreeCADClient(endpoint).execute("pass").status, "unknown")

    def test_malformed_execute_result_is_unknown(self):
        for response in (True, "done", {}, {"success": "true"}, {"success": 1}):
            with self.subTest(response=response), rpc_server(lambda code: response) as (endpoint, _):
                self.assertEqual(FreeCADClient(endpoint).execute("pass").status, "unknown")

    def test_timeout_does_not_imply_cancellation_or_retry(self):
        calls = []

        def delayed(code):
            calls.append(code)
            time.sleep(0.2)
            return {"success": True}

        with rpc_server(delayed) as (endpoint, _):
            start = time.monotonic()
            result = FreeCADClient(endpoint, timeout=0.04).execute("pass")
            elapsed = time.monotonic() - start
        self.assertEqual(result.status, "unknown")
        self.assertFalse(result.success)
        self.assertLess(elapsed, 0.18)
        self.assertEqual(calls, ["pass"])
        self.assertIn("inspect", result.message.lower())

    def test_disconnect_after_receipt_never_automatically_retries(self):
        with broken_http("disconnect") as (endpoint, calls):
            result = FreeCADClient(endpoint).execute("mutate_document()")
        self.assertEqual(result.status, "unknown")
        self.assertEqual(len(calls), 1)

    def test_http_error_and_invalid_xml_have_unknown_mutation_outcome(self):
        for mode in ("503", "malformed"):
            with self.subTest(mode=mode), broken_http(mode) as (endpoint, calls):
                result = FreeCADClient(endpoint).execute("pass")
            self.assertEqual(result.status, "unknown")
            self.assertEqual(len(calls), 1)

    def test_rpc_fault_is_redacted_and_unknown_for_mutation(self):
        def fault(code):
            raise Fault(42, "payload_secret leaked by remote server")

        with rpc_server(fault) as (endpoint, _), self.assertLogs("cortexcad.ipc") as logged:
            result = FreeCADClient(endpoint).execute("payload_secret = 1")
        self.assertEqual(result.status, "unknown")
        self.assertEqual(result.data["fault_code"], 42)
        self.assertNotIn("payload_secret", json.dumps(result.to_dict()))
        self.assertNotIn("payload_secret", "\n".join(logged.output))

    def test_refused_connection_is_offline(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            endpoint = f"http://127.0.0.1:{listener.getsockname()[1]}"
            result = FreeCADClient(endpoint, timeout=0.1).execute("pass")
        self.assertEqual(result.status, "offline")
        self.assertFalse(result.success)

    def test_invalid_code_fails_before_network(self):
        client = FreeCADClient()
        with patch("cortexcad.client.ServerProxy") as proxy:
            for code in ("", "  ", None, 23):
                with self.subTest(code=code), self.assertRaises(ValueError):
                    client.execute(code)
            proxy.assert_not_called()


class RecipeAndCliTests(unittest.TestCase):
    def test_preview_never_connects_or_claims_execution(self):
        with patch("cortexcad.client.ServerProxy") as proxy:
            result = preview_recipe("sketcher")
            proxy.assert_not_called()
        self.assertEqual(result.status, "offline")
        self.assertFalse(result.success)
        self.assertIn("recompute", result.script)

    def test_recipe_validation_precedes_ipc(self):
        with patch("cortexcad.client.ServerProxy") as proxy:
            with self.assertRaises(ValueError):
                FreeCADClient().run_recipe("arbitrary_python")
            proxy.assert_not_called()

    def test_cli_defaults_to_preview(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), patch("cortexcad.client.ServerProxy") as proxy:
            code = main(["run", "sketcher"])
            proxy.assert_not_called()
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "offline")

    def test_cli_rejects_duplicate_json_keys_before_ipc(self):
        output = io.StringIO()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as parameters:
            parameters.write('{"length": "invalid", "length": 60}')
            parameters.flush()
            with contextlib.redirect_stdout(output), patch("cortexcad.client.ServerProxy") as proxy:
                code = main(["run", "sketcher", "--parameters", parameters.name])
                proxy.assert_not_called()
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "error")

    def test_cli_doctor_returns_failure_exit_for_unreachable(self):
        output = io.StringIO()
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            endpoint = f"http://127.0.0.1:{listener.getsockname()[1]}"
            with contextlib.redirect_stdout(output), patch.dict(os.environ, {"CORTEXCAD_ENDPOINT": endpoint}):
                code = main(["doctor"])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "offline")


if __name__ == "__main__":
    unittest.main()
