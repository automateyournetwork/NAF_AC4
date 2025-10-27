#!/usr/bin/env python3
import json
import time
import subprocess
import threading
import sys

# -------- 1) Launch the MCP server subprocess (swap to your path if needed) -------
SERVER_CMD = ["python3", "server.py"]  # <- your FastMCP server file

mcp_proc = subprocess.Popen(
    SERVER_CMD,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1  # line-buffered
)

def _stderr_logger(proc):
    for line in proc.stderr:
        print("[MCP STDERR]", line.rstrip(), file=sys.stderr)

threading.Thread(target=_stderr_logger, args=(mcp_proc,), daemon=True).start()

# -------- 2) Minimal JSON-RPC helpers --------------------------------------------
_req_id = 0
def _next_id():
    global _req_id
    _req_id += 1
    return _req_id

def send(obj: dict):
    mcp_proc.stdin.write(json.dumps(obj) + "\n")
    mcp_proc.stdin.flush()

def recv(timeout=10):
    """Blocking line-read with a soft timeout."""
    start = time.time()
    while time.time() - start < timeout:
        line = mcp_proc.stdout.readline()
        if not line:
            # proc ended or no data yet
            time.sleep(0.02)
            continue
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            # skip junk line(s)
            continue
    raise TimeoutError("No JSON-RPC response from MCP server")

# -------- 3) MCP lifecycle + tool calls ------------------------------------------
def initialize():
    rid = _next_id()
    send({
        "jsonrpc": "2.0",
        "id": rid,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "multiply-demo-client", "version": "1.0"}
        }
    })
    # Wait for the initialize response
    while True:
        resp = recv()
        if resp.get("id") == rid:
            break

    # Then notify initialized
    send({
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    })

def tools_list():
    rid = _next_id()
    send({"jsonrpc": "2.0", "id": rid, "method": "tools/list"})
    while True:
        resp = recv()
        if resp.get("id") == rid:
            return resp.get("result", {}).get("tools", [])

def tools_call(name: str, arguments: dict):
    rid = _next_id()
    send({
        "jsonrpc": "2.0",
        "id": rid,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments}
    })
    while True:
        resp = recv()
        if resp.get("id") == rid:
            if "error" in resp:
                raise RuntimeError(resp["error"])
            return resp.get("result", {})

# -------- 4) Tiny REPL for multiply ----------------------------------------------
def main():
    try:
        print("[CLIENT] Initializing MCP…")
        initialize()
        time.sleep(0.1)

        tools = tools_list()
        names = [t["name"] for t in tools]
        print("[CLIENT] Tools available:", names)

        if "multiply" not in names:
            print("❌ 'multiply' tool not found. Make sure your server exposes it.")
            return

        print("\nType two numbers separated by space (or 'exit'):")
        while True:
            raw = input("> ").strip()
            if raw.lower() in ("exit", "quit"):
                break
            if not raw:
                continue

            try:
                a_str, b_str = raw.split()
                a = float(a_str)
                b = float(b_str)
            except Exception:
                print("Please enter two numbers, e.g. `3 7`")
                continue

            result = tools_call("multiply", {"a": a, "b": b})
            # Expect: {"a": ..., "b": ..., "product": ..., "summary": "..."}
            summary = result.get("summary") or f"{a} × {b} = {result.get('product')}"
            print(summary)

    finally:
        if mcp_proc:
            mcp_proc.terminate()
            try:
                mcp_proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                mcp_proc.kill()

if __name__ == "__main__":
    main()
