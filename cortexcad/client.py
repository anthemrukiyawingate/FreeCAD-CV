"""Typed, single-attempt XML-RPC boundary to the FreeCADMCP addon.

This module needs only the standard library. A socket timeout bounds individual
I/O waits; it cannot cancel a FreeCAD GUI task or bound OS DNS resolution. Use a
numeric loopback address with the documented SSH tunnel for predictable routing.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import http.client
import json
import logging
import math
import os
import socket
import time
from typing import Any, Literal
from urllib.parse import urlsplit
from uuid import uuid4
from xml.parsers.expat import ExpatError
from xmlrpc.client import Fault, ProtocolError, ResponseError, SafeTransport, ServerProxy, Transport

Status = Literal["ok", "offline", "error", "unknown"]
LOG = logging.getLogger("cortexcad.ipc")
DEFAULT_ENDPOINT = "http://127.0.0.1:9875"
DEFAULT_TIMEOUT = 5.0
MAX_TIMEOUT = 3600.0
MAX_SCRIPT_BYTES = 1_000_000
_UNKNOWN = "Execution outcome is unknown. Inspect the Windows FreeCAD document before retrying; no retry was sent."


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """Local outcome, separate from remote data and offline script previews.

    ``error`` never implies transaction rollback. ``unknown`` means the mutation
    may still be running or already have committed. Only ``ok`` is success.
    """

    status: Status
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    request_id: str = ""
    elapsed_ms: float = 0.0
    script: str | None = None

    @property
    def success(self) -> bool:
        return self.status == "ok"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible record, including the derived success flag."""
        return {**asdict(self), "success": self.success}


class _SingleAttemptTransport(Transport):
    """Disable Transport.request's automatic retry after dropped HTTP sockets."""

    def __init__(self, timeout: float, headers: tuple[tuple[str, str], ...] = ()) -> None:
        super().__init__(headers=headers)
        self.timeout = timeout

    def request(self, host: str, handler: str, request_body: bytes, verbose: bool = False) -> Any:
        return self.single_request(host, handler, request_body, verbose)

    def make_connection(self, host: str) -> http.client.HTTPConnection:
        connection = super().make_connection(host)
        connection.timeout = self.timeout
        return connection


class _SingleAttemptSafeTransport(SafeTransport):
    """HTTPS equivalent, retaining Python's default certificate verification."""

    def __init__(self, timeout: float, headers: tuple[tuple[str, str], ...] = ()) -> None:
        super().__init__(headers=headers)
        self.timeout = timeout

    def request(self, host: str, handler: str, request_body: bytes, verbose: bool = False) -> Any:
        return self.single_request(host, handler, request_body, verbose)

    def make_connection(self, host: str) -> http.client.HTTPSConnection:
        connection = super().make_connection(host)
        connection.timeout = self.timeout
        return connection


def _endpoint(value: str) -> str:
    """Reject embedded credentials and URL metadata without echoing the URL."""
    try:
        if not isinstance(value, str) or not value or any(char.isspace() for char in value):
            raise ValueError
        parts = urlsplit(value)
        if (parts.scheme not in ("http", "https") or not parts.hostname
                or parts.username is not None or parts.password is not None
                or parts.query or parts.fragment
                or parts.path not in ("", "/", "/RPC2")
                or (parts.port is not None and not 1 <= parts.port <= 65535)):
            raise ValueError
        return value
    except (ValueError, TypeError):
        raise ValueError("Endpoint must be an HTTP(S) host URL with a valid port and optional /RPC2; credentials, queries, and fragments are forbidden.") from None


def _timeout(value: float | str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("Timeout must be a finite number greater than zero and no more than 3600 seconds.") from None
    if isinstance(value, bool) or not math.isfinite(parsed) or not 0 < parsed <= MAX_TIMEOUT:
        raise ValueError("Timeout must be a finite number greater than zero and no more than 3600 seconds.")
    return parsed


class FreeCADClient:
    """One new connection and one RPC request per call, with no automatic retry.

    Arguments override CORTEXCAD_ENDPOINT and CORTEXCAD_TIMEOUT. An optional
    CORTEXCAD_TOKEN is transmitted only as a Bearer header. Client calls are live;
    preview_recipe is the separate, network-free offline path.
    """

    def __init__(self, endpoint: str | None = None, timeout: float | None = None) -> None:
        self.endpoint = _endpoint(os.environ.get("CORTEXCAD_ENDPOINT", DEFAULT_ENDPOINT) if endpoint is None else endpoint)
        self.timeout = _timeout(os.environ.get("CORTEXCAD_TIMEOUT", str(DEFAULT_TIMEOUT)) if timeout is None else timeout)
        token = os.environ.get("CORTEXCAD_TOKEN", "")
        if any(ord(char) < 33 or ord(char) > 126 for char in token):
            raise ValueError("CORTEXCAD_TOKEN must contain only visible ASCII characters without whitespace.")
        self._headers = (("Authorization", f"Bearer {token}"),) if token else ()

    def ping(self) -> ExecutionResult:
        """Check the bridge's ping method. This does not prove GUI/CAD readiness."""
        return self._call("ping")

    def execute(self, code: str) -> ExecutionResult:
        """Execute reviewed Python on the Windows GUI thread exactly once.

        Intended for trusted notebook code; this arbitrary-code method is not
        exposed through the MCP wrapper. Use run_recipe for bounded operations.
        """
        if not isinstance(code, str) or not code.strip():
            raise ValueError("Code must be a nonempty Python source string.")
        if len(code.encode("utf-8")) > MAX_SCRIPT_BYTES:
            raise ValueError("Code exceeds the one megabyte request limit.")
        return self._call("execute_code", code)

    def run_recipe(self, recipe: str, parameters: dict[str, object] | None = None) -> ExecutionResult:
        """Validate parameters locally, build the native script, then execute it."""
        from .recipes import build_script

        return self.execute(build_script(recipe, parameters))

    def _call(self, operation: Literal["ping", "execute_code"], *args: str) -> ExecutionResult:
        started = time.monotonic()
        request_id = uuid4().hex
        mutating = operation == "execute_code"
        transport_type = _SingleAttemptSafeTransport if self.endpoint.startswith("https:") else _SingleAttemptTransport
        transport = transport_type(self.timeout, self._headers)
        status: Status = "unknown" if mutating else "error"
        message = _UNKNOWN if mutating else "Bridge health could not be verified."
        data: dict[str, Any] = {}
        error_type: str | None = None
        try:
            with ServerProxy(self.endpoint, transport=transport, allow_none=True) as proxy:
                response = getattr(proxy, operation)(*args)
            if not mutating:
                if response is True:
                    status, message = "ok", "XML-RPC bridge answered ping; GUI geometry execution is not yet verified."
                else:
                    error_type = "InvalidPingResponse"
                    message = "Bridge returned an incompatible ping response; expected boolean true."
            elif not isinstance(response, dict) or type(response.get("success")) is not bool:
                error_type = "InvalidExecutionResponse"
            else:
                # XML-RPC also supports values that JSON cannot represent.
                # Fail closed rather than silently corrupting notebook/MCP data.
                json.dumps(response, allow_nan=False)
                data = response
                if response["success"]:
                    status, message = "ok", "FreeCAD bridge reported successful script completion."
                else:
                    remote_error = str(response.get("error", "")).lower()
                    remote_code = str(response.get("code", "")).upper()
                    if ("TIMEOUT" in remote_code or remote_code == "GUI_DISPATCH_STUCK"
                            or "timed out" in remote_error or "timeout" in remote_error):
                        status, message = "unknown", _UNKNOWN
                    else:
                        status = "error"
                        message = "FreeCAD reported an execution error; partial document changes may remain. Inspect the document before retrying."
                    error_type = "RemoteExecutionError"
        except (ConnectionRefusedError, socket.gaierror) as exc:
            status, message = "offline", "Could not connect to the bridge; this call did not execute a script. Check FreeCAD, the SSH tunnel, and the endpoint."
            error_type = type(exc).__name__
        except Fault as exc:
            # A fault might follow a partial mutation; do not promise rollback.
            error_type = "XMLRPCFault"
            data = {"fault_code": exc.faultCode}
        except (OSError, http.client.HTTPException, ProtocolError, ResponseError,
                ExpatError, TypeError, ValueError, OverflowError) as exc:
            error_type = type(exc).__name__
        finally:
            transport.close()
        elapsed_ms = round((time.monotonic() - started) * 1000, 3)
        result = ExecutionResult(status=status, message=message, data=data,
                                 request_id=request_id, elapsed_ms=elapsed_ms)
        # Logs deliberately contain neither payload/remote output nor exception
        # text: all three can contain credentials or arbitrary script content.
        parts = urlsplit(self.endpoint)
        event = {"event": "freecad_rpc", "request_id": request_id, "operation": operation,
                 "endpoint": f"{parts.scheme}://{parts.netloc}", "status": status,
                 "elapsed_ms": elapsed_ms, "attempts": 1, "error_type": error_type}
        LOG.log(logging.INFO if result.success else logging.WARNING, json.dumps(event, sort_keys=True))
        return result


def preview_recipe(recipe: str, parameters: dict[str, object] | None = None) -> ExecutionResult:
    """Validate and render a recipe without creating a connection or CAD object."""
    from .recipes import build_script

    script = build_script(recipe, parameters)
    return ExecutionResult(status="offline", message="Offline preview only. No connection was opened and no CAD geometry was created.",
                           data={"recipe": recipe}, script=script)
