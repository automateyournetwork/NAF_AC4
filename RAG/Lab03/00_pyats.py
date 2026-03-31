from genie.testbed import load
import json

# --- Load testbed file ---
testbed = load("testbed.yaml")

# --- Connect to Cat9k_AO_Sandbox ---
device = testbed.devices["Cat9k_AO_Sandbox"]
device.connect(log_stdout=True)

# --- Parse a command ---
parsed_output = device.parse("show ip interface brief")

# --- Pretty-print the parsed JSON ---
print("\n✅ Parsed 'show ip interface brief' (as JSON):\n")
print(json.dumps(parsed_output, indent=2))
