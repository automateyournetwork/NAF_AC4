from genie.testbed import load
from langchain_community.document_loaders import JSONLoader
from langchain.docstore.document import Document
import json
import tempfile
import os

# --- Step 1: Load testbed and connect to device ---
testbed = load("testbed.yaml")
device = testbed.devices["R1"]
device.connect(log_stdout=True)

# --- Step 2: Parse CLI output to JSON ---
parsed_output = device.parse("show ip route")
print("\n✅ Parsed output:\n")
print(json.dumps(parsed_output, indent=2))

# --- Step 3: Write parsed JSON to a temp file ---
with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w") as tmp:
    json.dump(parsed_output, tmp, indent=2)
    tmp_path = tmp.name

# --- Step 4: Load parsed JSON into LangChain documents ---
# Since top-level keys are interface names, we select the root
loader = JSONLoader(
    file_path=tmp_path,
    jq_schema='.',              # Entire JSON object (one doc per interface)
    text_content=False
)

documents = loader.load()
print(f"\n📄 Loaded {len(documents)} LangChain document(s) from parsed CLI output")

# Preview the first document
print("\n🔍 First Document Content:")
print(documents[0].page_content)
print("\n📎 Metadata:")
print(documents[0].metadata)

# --- Step 5: Clean up temp file ---
os.remove(tmp_path)
