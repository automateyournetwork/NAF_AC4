import os
import json
import time
import subprocess
import threading
from dotenv import load_dotenv
from openai import OpenAI

# === 1. Load Environment Variables ===

# Load .env file for sensitive values like your OpenAI API key
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set")

# Initialize the OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# === 2. Launch MCP subprocess ===

# Define the MCP server command — you can swap in a different MCP server here
FASTMCP_CMD = ["python3", "server.py"]

# Start the MCP server as a subprocess with pipes for stdin/stdout/stderr
mcp_proc = subprocess.Popen(
    FASTMCP_CMD,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=0  # Unbuffered to stream line-by-line
)

# Background thread to print MCP server stderr messages (e.g. logs or stack traces)
def log_stderr(proc):
    for line in proc.stderr:
        print("[MCP STDERR]", line.strip())

# Run stderr logging in the background
threading.Thread(target=log_stderr, args=(mcp_proc,), daemon=True).start()

# === 3. JSON-RPC Communication Utilities ===

# Keep track of JSON-RPC message IDs
request_id = 0
def next_id():
    global request_id
    request_id += 1
    return request_id

# Send a JSON-RPC request to the MCP server
def mcp_send(obj: dict):
    mcp_proc.stdin.write(json.dumps(obj) + "\n")
    mcp_proc.stdin.flush()

# Read a JSON-RPC response from the MCP server (blocking with timeout)
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

# Send required "initialize" and "initialized" messages per MCP protocol
def initialize_mcp():
    mcp_send({
        "jsonrpc": "2.0",
        "id": next_id(),
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "subnet-agent", "version": "1.0"}
        }
    })
    time.sleep(0.1)
    mcp_send({
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    })

# Ask the MCP server for its available tools (like DHCP for tool metadata)
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
            result = resp.get("result", {})
            return result.get("tools", [])

# Call a specific MCP tool by name, passing in arguments
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

# Convert a MCP tool into an OpenAI-compatible function schema
def tool_to_openai(tool: dict) -> dict:
    # MCP tools return `inputSchema`, which maps to OpenAI's `parameters`
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
    time.sleep(0.5)  # Give server a moment to fully initialize

    # Fetch and print the discovered tools
    tools = get_tool_list()
    print(f"[AGENT] Found tools: {[t['name'] for t in tools]}")

    # Convert all tools to OpenAI-compatible function definitions
    openai_tools = [tool_to_openai(t) for t in tools]

    # System prompt describing how the assistant should behave
    messages = [{
        "role": "system",
        "content": (
            "You are a helpful network assistant who explains CIDR notation IP addresses to users in detail. "
            "When asked for subnet calculations, call the `subnet_calculator` tool. Use the tool to get detailed "
            "subnet information for a given CIDR and then explain the results in a human-readable format. "
            "Please break down the fields to help the user understand the subnet details."
        )
    }]

    # REPL-style input loop
    while True:
        user_input = input("\nCIDR (or 'exit'): ").strip()
        if user_input.lower() == "exit":
            break

        messages.append({"role": "user", "content": user_input})
        print(f"[AGENT] User input: {user_input}")

        try:
            # Ask GPT to either respond or call a tool
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                functions=openai_tools,
                function_call="auto"
            )
            choice = response.choices[0].message
            print(f"[AGENT] OpenAI replied: {choice}")

            if choice.function_call:
                # Tool invocation requested by GPT
                fname = choice.function_call.name
                args = json.loads(choice.function_call.arguments)
                print(f"[AGENT] Calling MCP tool: {fname} with args: {args}")

                # Call the tool and get result
                tool_result = call_tool(fname, args)

                # Feed the tool result back into the chat context
                messages.append({"role": "assistant", "content": None, "function_call": choice.function_call})
                messages.append({"role": "function", "name": fname, "content": json.dumps(tool_result)})

                # Ask GPT to interpret the function result for a human
                final_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages
                )
                print("\nAgent:", final_response.choices[0].message.content)
                messages.append({"role": "assistant", "content": final_response.choices[0].message.content})

            else:
                # GPT replied directly without tool call
                print("\nAgent:", choice.content)
                messages.append({"role": "assistant", "content": choice.content})

        except Exception as e:
            error_msg = f"⚠️ Error during tool call or reply: {e}"
            print("\nAgent:", error_msg)
            messages.append({"role": "assistant", "content": error_msg})

# === 6. Script Entrypoint ===

if __name__ == "__main__":
    try:
        react_agent()
    finally:
        # Clean up the subprocess on exit
        if mcp_proc:
            mcp_proc.terminate()
            mcp_proc.wait()
