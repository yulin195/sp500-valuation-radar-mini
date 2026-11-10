"""Minimal MCP server over stdio (JSON-RPC 2.0, newline-delimited), stdlib only.

Implements the small subset needed here: initialize, notifications/initialized,
ping, tools/list, tools/call. It exposes the pure parts of Radar Mini only
(classification and CSV validation); it does no network I/O and reads no files.
"""

import json
import sys
from typing import Any

from radar_mini import __version__
from radar_mini.engine import classify
from radar_mini.loader import AnchorError, parse_anchors

PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {
        "name": "classify_anchor",
        "description": "Classify a close against one anchor. Returns the primary "
                       "tier (red/fair/yellow/watch/ok) and in_fair_range. "
                       "Observation aid only; not investment advice.",
        "inputSchema": {
            "type": "object",
            "properties": {k: {"type": "number"} for k in
                           ("close", "trigger", "fair_low", "fair_high")},
            "required": ["close", "trigger", "fair_low", "fair_high"],
        },
    },
    {
        "name": "validate_anchors_csv",
        "description": "Validate anchor CSV text. Reports the first malformed "
                       "row with its line number; never repairs input.",
        "inputSchema": {
            "type": "object",
            "properties": {"csv_text": {"type": "string"}},
            "required": ["csv_text"],
        },
    },
]


class ToolError(Exception):
    pass


def _num(args: dict[str, Any], name: str) -> float:
    v = args.get(name)
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ToolError(f"{name} must be a number")
    return float(v)


def call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "classify_anchor":
        c = classify(*(_num(args, k) for k in ("close", "trigger", "fair_low", "fair_high")))
        payload = {"tier": c.tier, "in_fair_range": c.in_fair_range}
    elif name == "validate_anchors_csv":
        text = args.get("csv_text")
        if not isinstance(text, str):
            raise ToolError("csv_text must be a string")
        try:
            rows = parse_anchors(text.splitlines(), source="csv_text")
            payload = {"valid": True, "rows": len(rows)}
        except AnchorError as exc:
            payload = {"valid": False, "error": str(exc)}
    else:
        raise ToolError(f"unknown tool: {name}")
    return {"content": [{"type": "text", "text": json.dumps(payload)}], "isError": False}


def handle(msg: dict[str, Any]) -> dict[str, Any] | None:
    """Return a response object, or None for notifications."""
    mid = msg.get("id")
    method = msg.get("method")
    if mid is None:
        return None  # notification (e.g. notifications/initialized)

    def ok(result): return {"jsonrpc": "2.0", "id": mid, "result": result}
    def err(code, message): return {"jsonrpc": "2.0", "id": mid,
                                    "error": {"code": code, "message": message}}

    if method == "initialize":
        return ok({"protocolVersion": PROTOCOL_VERSION,
                   "capabilities": {"tools": {}},
                   "serverInfo": {"name": "radar-mini", "version": __version__}})
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": TOOLS})
    if method == "tools/call":
        params = msg.get("params") or {}
        try:
            return ok(call_tool(params.get("name", ""), params.get("arguments") or {}))
        except ToolError as exc:
            return ok({"content": [{"type": "text", "text": str(exc)}], "isError": True})
    return err(-32601, f"method not found: {method}")


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            if not isinstance(msg, dict):
                raise ValueError
        except ValueError:
            resp = {"jsonrpc": "2.0", "id": None,
                    "error": {"code": -32700, "message": "parse error"}}
        else:
            resp = handle(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
