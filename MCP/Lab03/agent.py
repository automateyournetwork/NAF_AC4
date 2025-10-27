# pyats_agent.py

import os
import json
import time
import subprocess
import threading
from dotenv import load_dotenv
from openai import OpenAI

# === 1. Load Environment Variables ===
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set")

client = OpenAI(api_key=OPENAI_API_KEY)

# === 2. Launch MCP subprocess ===
FASTMCP_CMD = ["python3", "server.py"]

mcp_proc = subprocess.Popen(
    FASTMCP_CMD,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=0
)

def log_stderr(proc):
    for line in proc.stderr:
        print("[MCP STDERR]", line.strip())

threading.Thread(target=log_stderr, args=(mcp_proc,), daemon=True).start()

# === 3. JSON-RPC Communication Utilities ===
request_id = 0
def next_id():
    global request_id
    request_id += 1
    return request_id

def mcp_send(obj: dict):
    mcp_proc.stdin.write(json.dumps(obj) + "\n")
    mcp_proc.stdin.flush()

def mcp_recv(timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        line = mcp_proc.stdout.readline()
        if line.strip():
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
        time.sleep(0.05)
    raise TimeoutError("No response from MCP server")

# === 4. MCP Lifecycle ===
def initialize_mcp():
    mcp_send({
        "jsonrpc": "2.0",
        "id": next_id(),
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "pyats-agent", "version": "1.0"}
        }
    })
    time.sleep(0.1)
    mcp_send({"jsonrpc": "2.0", "method": "notifications/initialized"})

def get_tool_list() -> list:
    rid = next_id()
    mcp_send({
        "jsonrpc": "2.0",
        "id": rid,
        "method": "tools/list"
    })
    while True:
        resp = mcp_recv()
        if resp.get("id") == rid:
            return resp.get("result", {}).get("tools", [])

def call_tool(name: str, args: dict) -> dict:
    rid = next_id()
    mcp_send({
        "jsonrpc": "2.0",
        "id": rid,
        "method": "tools/call",
        "params": {
            "name": name,
            "arguments": args
        }
    })
    while True:
        resp = mcp_recv()
        if resp.get("id") == rid:
            if "error" in resp:
                raise RuntimeError(resp["error"])
            return resp.get("result", {})

def tool_to_openai(tool: dict) -> dict:
    schema = tool.get("inputSchema", {})
    return {
        "name": tool["name"],
        "description": tool.get("description", ""),
        "parameters": {
            "type": "object",
            "properties": schema.get("properties", {}),
            "required": schema.get("required", [])
        }
    }

# === 5. Main Loop: GPT + MCP Chat Agent ===
def react_agent():
    print("[AGENT] Initializing MCP + discovering tools...")
    initialize_mcp()
    time.sleep(0.5)

    tools = get_tool_list()
    print(f"[AGENT] Found tools: {[t['name'] for t in tools]}")
    openai_tools = [tool_to_openai(t) for t in tools]

    messages = [{
        "role": "system",
        "content": (
            "You are a Cisco network automation expert using pyATS. You can run commands like 'show ip interface brief',"
            " apply configurations, check logs, or ping from devices. When needed, call a tool like 'pyats_run_show_command'"
            " or 'pyats_configure_device'. Then interpret the result in a way that a junior network engineer can understand."
        )
    }]

    while True:
        user_input = input("\nAsk something (or 'exit'): ").strip()
        if user_input.lower() == "exit":
            break

        messages.append({"role": "user", "content": user_input})
        print(f"[AGENT] User input: {user_input}")

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                functions=openai_tools,
                function_call="auto"
            )
            choice = response.choices[0].message

            if choice.function_call:
                fname = choice.function_call.name
                args = json.loads(choice.function_call.arguments)
                print(f"[AGENT] Calling MCP tool: {fname} with args: {args}")

                tool_result = call_tool(fname, args)

                messages.append({"role": "assistant", "content": None, "function_call": choice.function_call})
                messages.append({"role": "function", "name": fname, "content": json.dumps(tool_result)})

                final_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages
                )
                print("\nAgent:", final_response.choices[0].message.content)
                messages.append({"role": "assistant", "content": final_response.choices[0].message.content})

            else:
                print("\nAgent:", choice.content)
                messages.append({"role": "assistant", "content": choice.content})

        except Exception as e:
            error_msg = f"\u26a0\ufe0f Error during tool call or reply: {e}"
            print("\nAgent:", error_msg)
            messages.append({"role": "assistant", "content": error_msg})

# === 6. Script Entrypoint ===
if __name__ == "__main__":
    try:
        react_agent()
    finally:
        if mcp_proc:
            mcp_proc.terminate()
            mcp_proc.wait()