# S0-IPC / S0-MCP test-first evidence

Task packet: Senior AI Developer and QA Auditor. Define falsifying tests, implement typed boundaries, document interfaces, package an optional stdio adapter, and audit failure behavior. Evidence date: 2026-10-03. No Windows workstation was contacted.

## Red: tests preceded implementations

`tests/test_client.py` and `tests/test_mcp_server.py` were written before the four client/package/CLI/MCP implementation files. The initial commands were:

```bash
python3 -m unittest discover -s tests -p 'test_client.py' -v
python3 -m unittest discover -s tests -p 'test_mcp_server.py' -v
```

Observed failures, before implementation:

```text
test_client ... ERROR
ModuleNotFoundError: No module named 'cortexcad.client'
Ran 1 test in 0.000s
FAILED (errors=1)

test_mcp_server ... ERROR
ModuleNotFoundError: No module named 'cortexcad.mcp_server'
Ran 1 test in 0.000s
FAILED (errors=1)
```

This initial red run proves the suite existed before the modules; it is an import failure, not evidence that each assertion individually failed. The subsequent targeted regression below demonstrates a behavior-level red/green cycle.

## Green: actual local transport tests

After implementation, the default execution sandbox prevented local socket creation (`PermissionError: [Errno 1] Operation not permitted`). That failed run was an environment restriction, not a passing transport test. An automatically approved escalation allowed the same tests to create ephemeral listeners bound exclusively to `127.0.0.1`; no external CAD engine was accessed.

```text
python3 -m unittest discover -s tests -p 'test_client.py' -v
Python 3.14.8
Ran 21 tests in 0.346s
OK
```

The delayed mutation test configured a 40 ms socket timeout against a 200 ms fake handler. The recorded JSON diagnostic reported `elapsed_ms: 40.696`, `error_type: TimeoutError`, `attempts: 1`, `status: unknown`. The fake handler recorded exactly one received script. A distinct HTTP peer consumed the entire request then disconnected without a response; it likewise observed exactly one request. This test specifically catches the stdlib transport's hidden retry if the single-attempt override is removed.

The 21 tests also cover exact-boolean health responses, upstream single-argument invocation, explicit remote errors, GUI stuck/legacy timeout responses, malformed result structures, invalid XML, HTTP errors, fault-message redaction, connection refusal, token headers, JSON logs, invalid endpoint/timeouts, preflight validation, default CLI previews, and failure exit codes.

## Behavior-level red/green: SDK coercion

The optional MCP SDK was installed only into a temporary test virtual environment. Tested versions: Python 3.14.8, `mcp` 1.30.0, `pydantic` 2.13.5.

After the initial six MCP function/registration contracts passed, two additional integration tests were added before fixing the discovered boundary issue. The failing test submitted `{"length": true}` through the real SDK and required it to be rejected. With `dict[str, float]`, SDK model validation silently converted the boolean to `1.0`, defeating the recipe validator's boolean rejection.

```text
/tmp/cortexcad-ipc-venv/bin/python -m unittest discover -s tests -p test_mcp_server.py -v
test_sdk_does_not_coerce_boolean_dimensions ... FAIL
AssertionError: ToolError not raised
Ran 8 tests in 1.568s
FAILED (failures=1)
```

Implementation changed the MCP parameter boundary to `dict[str, object]`, preserving raw types for the recipe validator. The same suite then reported:

```text
test_sdk_does_not_coerce_boolean_dimensions ... ok
test_stdio_handshake_preview_and_live_fake_bridge ... ok
Ran 8 tests in 1.514s
OK
```

The stdio test uses the actual MCP `ClientSession`, starts `python -m cortexcad.mcp_server`, initializes protocol negotiation, discovers exactly three bounded tools, checks bridge ping, gets an offline default preview, rejects an arbitrary recipe name without executing it, and sends one explicit live recipe to a real local XML-RPC fake server. The fake does not run the generated CAD source.

Static lint with Ruff 0.16.10 passed for all six owned Python implementation/test files. Package version is 0.1.0rc1, aligned with `pyproject.toml`.

The project virtual environment subsequently reproduced both suites on the minimum supported host generation, Python 3.12.3 with MCP 1.30.0:

```text
.venv/bin/python -m unittest discover -s tests -p test_client.py -v
Ran 21 tests in 0.341s
OK

.venv/bin/python -m unittest discover -s tests -p test_mcp_server.py -v
Ran 8 tests in 3.341s
OK
```

All 29 owned tests passed with no skips in this configured environment.

## Falsification audit and retained limits

| Claim | Falsifier / observation | Result |
| --- | --- | --- |
| Offline preview never creates geometry | Patched proxy must remain unused; status must be offline and success false | Pass |
| A TCP listener alone is insufficient health evidence | Truthy strings, integers, dicts, and false ping responses must fail | Pass |
| Mutations are never replayed automatically | Peer consumes request and drops response; count received payloads | Exactly one |
| Timeout does not prove cancellation | Handler continues longer than client budget | Unknown result; no retry |
| Malformed/faulted responses cannot claim success | Fake structures/XML/HTTP/fault responses | Unknown mutation result |
| Known failures do not guarantee rollback | Explicit false response | Error message requires partial-change inspection |
| Credentials and source are absent from logs | Token and source sentinels searched in captured JSON events | Absent |
| SDK typing cannot weaken geometric validation | Boolean dimension passed through real SDK | Rejected after observed regression |
| MCP does not expose arbitrary code | Wire-level tool enumeration and invalid recipe | Exactly three bounded tools |
| Windows geometry is valid and hardware fits | Requires actual FreeCAD/Windows and measured fixtures | **Not tested; release gate remains open** |

Timeouts are per socket operation, not absolute deadlines; DNS and slow response streaming remain outside that guarantee. HTTPS has a separate single-attempt implementation but no real certificate-server integration test in this suite. The bridge's upstream source was inspected at `main`; DevOps must pin and record its deployed commit. SDK-absent environments intentionally skip three optional SDK tests; install `.[mcp]` to enforce the full set. No live Windows, SSH routing, FreeCAD GUI, mechanical-load, physical-fit, GitHub publication, or Claude client acceptance is asserted.

## Final boundary review: strict live flag and duplicate JSON keys

Root integration review requested two additional falsification cases. Before the fixes, three new targeted tests produced 12 failing subcases: duplicate CLI JSON keys were silently overwritten, and the MCP SDK coerced non-boolean live values. After adding an object-pairs duplicate-key check and preserving the live value's original type until an exact boolean check, `PYTHONPATH=tests .venv/bin/python -m unittest test_client test_mcp_server -v` passed **32 tests** on Python 3.12.3 (22 client, 10 MCP) with no skips. Strings, numbers and null cannot trigger live execution. This supplements the earlier 29-test historical record; the final integrated count appears in QA_REPORT.md.
