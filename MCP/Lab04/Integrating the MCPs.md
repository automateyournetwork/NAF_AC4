# Integrating MCP Servers with Popular MCP Clients

## Prerequisites

Before configuring either client, replace `<homedir>` in all paths below with your actual WSL home directory username (e.g., `/home/jsmith/NAF_AC4/...`).

---

## Option 1: VS Code (with GitHub Copilot)

### Step 1 — Open MCP Configuration
1. Open the Command Palette: **Ctrl+Shift+P** (Windows/Linux) or **Cmd+Shift+P** (Mac)
2. Type **"MCP"** and select **MCP: Open User Configuration**

This opens your VS Code MCP config file.

### Step 2 — Add the MCP Servers
Paste the following into the config file, updating `<homedir>` for each path:

```json
{
  "servers": {
    "Multiply2Numbers": {
      "type": "stdio",
      "command": "wsl",
      "args": [
        "env",
        "python3",
        "/home/<homedir>/NAF_AC4/Lab01/server.py"
      ]
    },
    "subnet-calculator": {
      "type": "stdio",
      "command": "wsl",
      "args": [
        "env",
        "python3",
        "/home/<homedir>/NAF_AC4/Lab02/server.py"
      ]
    },
    "pyats": {
      "type": "stdio",
      "command": "wsl",
      "args": [
        "env",
        "PYATS_TESTBED_PATH=/home/<homedir>/NAF_AC4/Lab03/testbed.yaml",
        "python3",
        "/home/<homedir>/NAF_AC4/Lab03/server.py"
      ]
    }
  }
}
```

### Step 3 — Enable and Use the Tools
1. Save the config file
2. Open **GitHub Copilot Chat** in VS Code
3. Switch to **Agent mode** using the mode selector in the chat panel
4. Click the **Tools** button (🔧) — you should see your three MCP servers listed
5. Enable the ones you want to use, then start chatting!

> **Tip:** If your servers don't appear, open the Command Palette and run **MCP: List Servers** to check their status, or **MCP: Restart Server** to reinitialise a specific one.

---

## Option 2: Claude Desktop

### Step 1 — Install Claude Desktop
Download and install Claude Desktop from [https://claude.ai/download](https://claude.ai/download).

### Step 2 — Open the Config File
1. Launch Claude Desktop
2. Go to **Settings → Developer**
3. Click **Edit Config** — this opens `claude_desktop_config.json` in your default editor

Alternatively, open the file directly in VS Code:

| Platform | Path |
|----------|------|
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |

### Step 3 — Add the MCP Servers
Edit the file so it contains the following, updating `<homedir>` for each path:

```json
{
  "mcpServers": {
    "Multiply2Numbers": {
      "command": "wsl",
      "args": [
        "env",
        "python3",
        "/home/<homedir>/NAF_AC4/Lab01/server.py"
      ]
    },
    "subnet-calculator": {
      "command": "wsl",
      "args": [
        "env",
        "python3",
        "/home/<homedir>/NAF_AC4/Lab02/server.py"
      ]
    },
    "pyats": {
      "command": "wsl",
      "args": [
        "env",
        "PYATS_TESTBED_PATH=/home/<homedir>/NAF_AC4/Lab03/testbed.yaml",
        "python3",
        "/home/<homedir>/NAF_AC4/Lab03/server.py"
      ]
    }
  }
}
```

### Step 4 — Restart and Verify
1. **Fully quit** Claude Desktop (don't just close the window — use the system tray or `Cmd+Q`)
2. Relaunch Claude Desktop
3. Start a new conversation — you should see a **🔨 tools** indicator showing your MCP servers are available

> **Tip:** If a server fails to load, Claude Desktop will show an error icon next to it. Double-check your paths and that WSL is running correctly by testing the command in a terminal first:
> ```bash
> wsl env python3 /home/<homedir>/NAF_AC4/Lab01/server.py
> ```

