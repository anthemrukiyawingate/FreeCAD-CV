"""Optional MCP SDK stdio adapter exposing only the bounded curriculum tools."""
from __future__ import annotations

import logging
import sys
from typing import Any, Literal

from .client import FreeCADClient, preview_recipe

RecipeName = Literal["sketcher", "csg", "parametric", "capstone"]


def ping() -> dict[str, Any]:
    """Check the XML-RPC bridge. Success does not certify GUI/CAD readiness."""
    return FreeCADClient().ping().to_dict()


def curriculum_preview(recipe: RecipeName, parameters: dict[str, object] | None = None) -> dict[str, Any]:
    """Validate dimensions and preview FreeCAD code without creating geometry."""
    return preview_recipe(recipe, parameters).to_dict()


def curriculum_run(recipe: RecipeName, parameters: dict[str, object] | None = None,
                   live: object = False) -> dict[str, Any]:
    """Run one bounded recipe with JSON live=true; JSON false returns an offline preview.

    Other JSON types are rejected; strings and numbers never confirm execution.
    Inspect an unknown outcome on the Windows workstation before any retry.
    Example dimensions are teaching fixtures, not measured hardware fit.
    """
    # Preserve raw input through the SDK; a bool annotation coerces "true"/1.
    if type(live) is not bool:
        raise ValueError("live must be an exact JSON boolean; use true to execute or false to preview.")
    if live is not True:
        return curriculum_preview(recipe, parameters)
    return FreeCADClient().run_recipe(recipe, parameters).to_dict()


def create_server() -> Any:
    """Load the optional SDK lazily, keeping notebook and CLI installs minimal."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        raise RuntimeError("Install the optional MCP SDK with: python -m pip install -e '.[mcp]'") from None
    server = FastMCP("CortexCAD")
    server.tool()(ping)
    server.tool()(curriculum_preview)
    server.tool()(curriculum_run)
    return server


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)
    try:
        server = create_server()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    server.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
