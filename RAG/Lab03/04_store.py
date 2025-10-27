from genie.testbed import load
from langchain_community.document_loaders import JSONLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import tempfile
import json
import os
import uuid

# --- Step 1: Connect to device and get parsed JSON ---
testbed = load("testbed.yaml")
device = testbed.devices["R1"]
device.connect(log_stdout=True)
parsed_output = device.parse("show ip route")

# --- Step 2: Write parsed JSON to temp file ---
with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w") as tmp:
    json.dump(parsed_output, tmp, indent=2)
    tmp_path = tmp.name

# --- Step 3: Load JSON into LangChain Documents ---
loader = JSONLoader(
    file_path=tmp_path,
    jq_schema='.',              # Entire JSON object (one doc per interface)
    text_content=False
)

documents = loader.load()

os.remove(tmp_path)  # Clean up temp file

# --- Step 4: Embed & Split ---
embedding = OpenAIEmbeddings(model="text-embedding-3-small")
semantic_splitter = SemanticChunker(embedding)
semantic_chunks = semantic_splitter.split_documents(documents)

print(f"🧠 Total routing chunks created: {len(semantic_chunks)}")

# --- Store 1: In-Memory Chroma ---
print("\n💾 Creating in-memory Chroma store...")
memory_db = Chroma.from_documents(semantic_chunks, embedding)
print("📥 In-memory Chroma store created!")

# Explore in-memory contents
raw_memory_data = memory_db._collection.get()
print(f"📊 In-memory: {len(raw_memory_data['documents'])} documents")
print(f"🆔 Sample IDs: {raw_memory_data['ids'][:2]}")
print(f"📄 First Document Snippet:\n{raw_memory_data['documents'][0][:300]}...\n")

# --- Store 2: Persistent Chroma Store ---
print("\n💽 Creating persistent Chroma store...")

session_id = str(uuid.uuid4())
persist_path = f"chroma_routes_{session_id}"

persistent_db = Chroma.from_documents(
    semantic_chunks,
    embedding,
    persist_directory=persist_path
)
persistent_db.persist()

print(f"📁 Persistent Chroma DB saved to: {persist_path}")

# Explore persistent contents
raw_persist_data = persistent_db._collection.get()
print(f"📊 Persistent: {len(raw_persist_data['documents'])} documents")
print(f"🆔 Sample IDs: {raw_persist_data['ids'][:2]}")
print(f"📄 First Document Snippet:\n{raw_persist_data['documents'][0][:300]}...\n")
