"""Test harness para scripts/mcp_server.py via stdio con espera activa."""
import json
import select
import subprocess
import sys
import threading
import time
from pathlib import Path

VENV = "/tmp/mcp-venv/bin/python3"
SCRIPT = str(Path(__file__).resolve().parent / "mcp_server.py")


def run_test(calls, expect=4, timeout=15):
    p = subprocess.Popen(
        [VENV, SCRIPT],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    def write():
        for c in calls:
            p.stdin.write(json.dumps(c) + "\n")
            p.stdin.flush()
            time.sleep(0.2)
        p.stdin.close()

    t = threading.Thread(target=write)
    t.start()

    responses = []
    deadline = time.time() + timeout
    while len(responses) < expect and time.time() < deadline:
        rd, _, _ = select.select([p.stdout], [], [], 0.5)
        if rd:
            line = p.stdout.readline()
            if line.strip():
                try:
                    responses.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        else:
            if p.poll() is not None:
                break

    t.join(timeout=5)
    try:
        p.terminate()
    except Exception:
        pass
    p.wait(timeout=5)
    return responses


CALLS = [
    {"jsonrpc": "2.0", "id": 1, "method": "initialize",
     "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                 "clientInfo": {"name": "test", "version": "0.1"}}},
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
     "params": {"name": "list_games", "arguments": {}}},
    {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
     "params": {"name": "list_enemies", "arguments": {"game": "ff9", "group": "jefes"}}},
    {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
     "params": {"name": "search_guide", "arguments": {"game": "ff9", "query": "Ozma", "max_results": 3}}},
    {"jsonrpc": "2.0", "id": 6, "method": "tools/call",
     "params": {"name": "find_item", "arguments": {"game": "ff9", "item_name": "Pimienta Letal"}}},
]


if __name__ == "__main__":
    resps = run_test(CALLS, expect=6)
    print(f"Recibidas {len(resps)} respuestas")
    for r in resps:
        rid = r.get("id")
        if rid in (3, 4, 5, 6):
            content = r.get("result", {}).get("content", [])
            if content:
                print(f"\n=== id={rid} ===")
                print(content[0]["text"][:1500])
        else:
            print(f"\n=== id={rid} (meta) ===")
            print(json.dumps(r, ensure_ascii=False)[:200])