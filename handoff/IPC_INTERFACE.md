# S0-IPC / S0-MCP interface contract

Release candidate: 0.1.0rc1. Linux automation requires Python 3.12+. The generated native recipes target FreeCAD's Python 3.11+ runtime. The stdlib notebook client imports no FreeCAD or MCP modules.

## Verified upstream protocol

The reference is [neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp). Its current `main` source was inspected on 2026-10-03; this source review is not a Windows execution test or a pinned dependency release. DevOps must record the installed addon commit and repeat compatibility tests before workstation acceptance.

The inspected [addon RPC implementation](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/rpc_server.py) defines `ping() -> True` and `execute_code(code, timeout=None) -> dict`. Successful execution reports `success: true` plus a message containing captured stdout. Failure reports `success: false` and an error, sometimes a dispatch code. Execution runs on the GUI thread. The [dispatch health implementation](https://github.com/neka-nat/freecad-mcp/blob/main/addon/FreeCADMCP/rpc_server/dispatch_health.py) marks an uninterruptible timed-out task with `GUI_DISPATCH_STUCK`.

CortexCAD calls `execute_code` with one positional source argument, preserving compatibility with older addons that lack the optional timeout argument. It does not call `execute`, send raw socket JSON, or speak MCP over port 9875. Its local stdio wrapper uses the [official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x), currently bounded to the 1.x API by the package extra.

## Configuration

| Setting | Default | Contract |
| --- | --- | --- |
| `CORTEXCAD_ENDPOINT` | `http://127.0.0.1:9875` | HTTP(S), valid hostname/IP and port; path empty, `/`, or `/RPC2`. No URL credentials, query, or fragment. |
| `CORTEXCAD_TIMEOUT` | `5` | Finite seconds, greater than zero and at most 3600. Boolean values are invalid. |
| `CORTEXCAD_TOKEN` | Unset | Optional Bearer token header; visible ASCII with no whitespace. Never passed in a URL or log event. |
| `CORTEXCAD_LIVE` | Unset | Notebook convention only. The client does not silently change modes based on this variable. |

Explicit constructor arguments override endpoint/timeout environment values. Invalid configuration raises `ValueError` before networking. Use the numeric loopback endpoint through the README's SSH tunnel. HTTPS retains Python certificate verification; TLS is not provided by the upstream HTTP addon itself and would need an independently managed terminator.

The timeout applies to blocking socket operations. OS DNS resolution and a peer slowly delivering a response can exceed this duration in total. It is **not a hard end-to-end deadline or cancellation request**. The upstream GUI may continue after a client timeout. The client does not extend its socket timeout to match the upstream GUI budget. DevOps should set a suitable budget for known workloads before the first run, inspect uncertain outcomes, and never automatically replay a mutation.

## Python API

```python
from cortexcad import FreeCADClient, preview_recipe

preview = preview_recipe("sketcher", {"length": 60.0, "width": 40.0, "height": 6.0})
assert preview.status == "offline" and not preview.success
print(preview.script)  # Review the generated source; no CAD object exists yet.

client = FreeCADClient(endpoint="http://127.0.0.1:9875", timeout=5.0)
health = client.ping()                  # Live, read-only bridge check.
# After explicitly choosing live execution:
# result = client.run_recipe("sketcher", {"length": 60.0})
# print(result.to_dict())
```

| Interface | Return / behavior |
| --- | --- |
| `FreeCADClient(endpoint: str \| None = None, timeout: float \| None = None)` | Validate configuration; no network request. |
| `client.ping()` | `ExecutionResult`; only exact boolean `True` is accepted as a compatible ping. This does not verify GUI health or geometry. |
| `client.execute(code: str)` | Live execution of trusted Python, at most 1 MB UTF-8; a blank or invalid source value raises `ValueError`. This method is not exposed through MCP. |
| `client.run_recipe(recipe, parameters=None)` | `build_script` validates phase and dimensions locally, then sends the result exactly once. |
| `preview_recipe(recipe, parameters=None)` | Validate and return the script with `offline` status; no client or socket is created. |
| `ExecutionResult.to_dict()` | JSON-compatible record including `status`, `success`, `message`, `data`, `request_id`, `elapsed_ms`, `script`. |

`cortexcad.recipes.build_script(phase, params=None) -> str` accepts `sketcher`, `csg`, `parametric`, or `capstone`. See that module and the phase lessons for exact parameter keys. Unrecognized phases/keys, booleans, strings, nonfinite numbers, impossible geometry, and out-of-bounds dimensions fail before IPC. Native recipes recompute, validate their final shapes, and refuse to overwrite their deterministic document names. Their own transaction handling does not make arbitrary `execute` scripts transactional.

### Status semantics

| Status | Meaning | Caller action |
| --- | --- | --- |
| `ok` | Compatible response reports success. | Inspect native recipe assertions/output; physical acceptance is separate. |
| `offline` | Explicit preview, refused connection, or DNS lookup failure. | Read `message`/`script` to distinguish preview from inability to connect. No successful CAD claim. |
| `error` | Invalid health response or explicit completed remote execution failure. | Inspect the document for partial changes; no rollback guarantee. |
| `unknown` | A mutation response is missing, malformed, timed out, faulted, or reports stuck execution. | Inspect Windows before any retry; execution may still be running or already have committed. |

Only `status == "ok"` makes `success` true. A preview is useful but is not CAD success. A connection refusal is safely offline because the connection never opened. Other transport failures remain conservative because their execution outcome cannot be inferred.

The transport calls `single_request` directly, bypassing Python `xmlrpc.client.Transport.request`'s automatic connection retry. HTTPS uses the same single-attempt policy. Every operation receives a fresh connection and closes it after the call. A lost response is never resent automatically. `request_id` is local diagnostics metadata; it is not a remote idempotency key.

### Structured diagnostics

Logger `cortexcad.ipc` emits one JSON event per attempted RPC with `event`, `request_id`, `operation`, sanitized endpoint authority, `status`, `elapsed_ms`, `attempts: 1`, and `error_type`. Exception strings, authorization headers, source payloads, remote messages, and script output are excluded. The CLI and MCP process route logs to stderr. Libraries use the caller's logging configuration.

The returned `data` may include the remote output the caller requested, including recipe assertion summaries. Treat it as untrusted data. It is deliberately not logged. Offline `script` is likewise intentionally included for review. Do not put secrets in source or publish raw result records without reviewing them. XML-RPC fault text is discarded; only its numeric fault code is retained.

## CLI and MCP

```bash
python -m cortexcad doctor
python -m cortexcad run sketcher
python -m cortexcad run capstone --parameters Projects/CAPSTONE_Plato_Shadows_Hardware_Mounts/measurement.example.json --dry-run
# Explicit live execution after reviewing the preview and checking the workstation:
python -m cortexcad run sketcher --live
```

CLI stdout contains exactly one JSON result. Exit status is 0 for a successful preview or an `ok` live operation; it is 2 for configuration errors or unsuccessful live operations. A preview's JSON still says `offline` and `success: false`. Parameter files must be JSON objects no larger than 64 KiB. `--live` and `--dry-run` are mutually exclusive. The default is a preview even when `CORTEXCAD_LIVE=1` is set.

```bash
python -m pip install -e '.[mcp]'
python -m cortexcad.mcp_server
```

The MCP server exclusively exposes `ping`, `curriculum_preview(recipe, parameters=None)`, and `curriculum_run(recipe, parameters=None, live=False)`. `live=true` is needed for a mutation. Unknown outcomes stay unknown in tool results. Recipe names are enumerated in the tool schema and validated again by the recipe builder. Parameters preserve their raw JSON value types through SDK validation so `true` cannot become `1.0`. The optional SDK is loaded only when creating the server; without it the launcher prints the installation command to stderr and exits 2. No arbitrary Python, shell, file export, deployment, or Git operations are exposed.

## Acceptance boundaries

Real local TCP/XML-RPC fake servers verify serialization, protocol dispatch, failure handling, timeout return, and lack of retries. The real MCP SDK initializes a stdio subprocess, discovers its tools, previews a recipe, rejects invalid recipe names, and executes exactly once against a loopback fake bridge. This does not execute FreeCAD or validate Windows, GUI dispatch, geometry, mechanical strength, hardware fit, tunnel/firewall setup, or a configured AI client. Those acceptance gates belong in the DevOps workstation record; deployment and release transfers remain with their designated teams.

See [recorded TDD evidence](IPC_TDD.md) for commands, the observed initial failures, and green results.
