"""JSON CLI for connectivity checks and curriculum recipe previews/execution."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys
from typing import Sequence

from .client import ExecutionResult, FreeCADClient, preview_recipe


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Parameter JSON must not contain duplicate keys.")
        result[key] = value
    return result


def _parameters(path: Path | None) -> dict[str, object] | None:
    if path is None:
        return None
    if path.stat().st_size > 65_536:
        raise ValueError("Parameter JSON file exceeds the 64 KiB limit.")
    result = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    if not isinstance(result, dict):
        raise ValueError("Parameter JSON must be an object.")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    from .recipes import PHASES

    parser = argparse.ArgumentParser(description="CortexCAD: preview safely, execute explicitly")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Verify XML-RPC ping; does not prove FreeCAD geometry readiness")
    run = commands.add_parser("run", help="Preview or execute a validated curriculum recipe")
    run.add_argument("recipe", choices=PHASES)
    run.add_argument("--parameters", type=Path, metavar="JSONFILE")
    mode = run.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Preview only (default)")
    mode.add_argument("--live", action="store_true", help="Create geometry in the connected FreeCAD instance")
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            result = FreeCADClient().ping()
            exit_code = 0 if result.success else 2
        else:
            parameters = _parameters(args.parameters)
            if args.live:
                result = FreeCADClient().run_recipe(args.recipe, parameters)
                exit_code = 0 if result.success else 2
            else:
                result = preview_recipe(args.recipe, parameters)
                exit_code = 0  # Preview generation succeeded; CAD status stays offline.
    except (ValueError, OSError, UnicodeError) as exc:
        # File paths and parser exception payloads can contain user data.
        result = ExecutionResult(status="error", message="Invalid configuration or recipe parameters, or parameter file could not be read.",
                                 data={"error_type": type(exc).__name__})
        exit_code = 2
    print(json.dumps(result.to_dict(), indent=2, allow_nan=False))
    return exit_code


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)
    raise SystemExit(main())
