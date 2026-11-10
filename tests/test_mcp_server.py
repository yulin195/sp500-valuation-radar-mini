"""Smoke test: spawn the MCP server as a subprocess and round-trip over stdio."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def rpc(i, method, params=None):
    m = {"jsonrpc": "2.0", "id": i, "method": method}
    if params is not None:
        m["params"] = params
    return json.dumps(m)


class McpSmokeTest(unittest.TestCase):
    def test_initialize_list_and_call(self):
        lines = [
            rpc(1, "initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                  "clientInfo": {"name": "t", "version": "0"}}),
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
            rpc(2, "tools/list"),
            rpc(3, "tools/call", {"name": "classify_anchor", "arguments": {
                "close": 120, "trigger": 100, "fair_low": 110, "fair_high": 130}}),
            rpc(4, "tools/call", {"name": "validate_anchors_csv", "arguments": {
                "csv_text": "ticker,trigger,fair_low,fair_high,sector,cap_tier\n"
                            "AAA,100,90,130,S,mega\n"}}),
            rpc(5, "tools/call", {"name": "classify_anchor", "arguments": {"close": "x"}}),
            rpc(6, "nope"),
        ]
        p = subprocess.run([sys.executable, str(ROOT / "mcp_server.py")], cwd=ROOT,
                           input="\n".join(lines) + "\n", capture_output=True,
                           text=True, timeout=30)
        self.assertEqual(p.returncode, 0, p.stderr)
        out = [json.loads(x) for x in p.stdout.splitlines()]
        self.assertEqual([o["id"] for o in out], [1, 2, 3, 4, 5, 6])  # no reply to the notification
        self.assertEqual(out[0]["result"]["serverInfo"]["name"], "radar-mini")
        self.assertEqual({t["name"] for t in out[1]["result"]["tools"]},
                         {"classify_anchor", "validate_anchors_csv"})
        self.assertEqual(json.loads(out[2]["result"]["content"][0]["text"]),
                         {"tier": "watch", "in_fair_range": True})
        v = json.loads(out[3]["result"]["content"][0]["text"])
        self.assertFalse(v["valid"])
        self.assertIn("line 2", v["error"])
        self.assertTrue(out[4]["result"]["isError"])
        self.assertEqual(out[5]["error"]["code"], -32601)


if __name__ == "__main__":
    unittest.main()
