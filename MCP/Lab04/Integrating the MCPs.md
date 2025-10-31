# Integrating the MCP Servers we have built with popular MCP clients 

## VS Code
You are already using VS Code for these labs. 

Open the Command Palette (Ctrl+Shift+P or Cmd+Shift+P on Mac) and type "MCP" to see the available commands. You can use these commands to interact with the MCP server.

We want MCP: Open User Configuration 

This will open a new file where you can add your MCP server details.

Add the following MCPs: 

```json
"Multiply2Numbers": {
	"type": "stdio",
	"command": "wsl",
	"args": [
		"env",
		"python3",
		"/home/<homedir>/NAF_AC4/Lab01/server.py"
	],
},
"subnet-calculator": {
	"type": "stdio",
	"command": "wsl",
	"args": [
		"env",
		"python3",
	    "/home/<homedir>/NAF_AC4/Lab02/server.py"
	],
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

Start the MCP Server

Launch Copilot and you should see the MCPs available as tools - enable them and use them!

```
## Claude Desktop 
Install Claude Desktop from https://claude.ai/download

Click along and install the tool - go into the Settings - Developer - Click Settings which will take you to the 

claude_desktop_config.json file 

Edit this in VS Code and add the MCPs

Check Claude Desktop (relaunch if needed) and you should see the MCPs available as tools

## Gemini-CLI 

Install Gemini-CLI from https://github.com/google-gemini/gemini-cli

Then visit root/.gemini and update the settings.json file to add the MCPs