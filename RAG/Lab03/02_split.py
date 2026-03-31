from genie.testbed import load
from langchain_community.document_loaders import JSONLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
import tempfile
import json
import os

# --- Step 1: Connect to device and get parsed JSON ---
testbed = load("testbed.yaml")
device = testbed.devices["Cat9k_AO_Sandbox"]
device.connect(log_stdout=True)
parsed_output = device.parse("show ip interface brief")

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
print(f"\n📄 Loaded {len(documents)} routing documents\n")

# --- SPLIT 1: RecursiveCharacterTextSplitter ---
print("🔹 Splitting with RecursiveCharacterTextSplitter")
recursive_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
recursive_chunks = recursive_splitter.split_documents(documents)
print(f"🔹 Recursive: {len(recursive_chunks)} chunks")

for i, chunk in enumerate(recursive_chunks[:2]):
    print(f"\n🧩 Recursive Chunk {i+1}:\n{chunk.page_content[:300]}...\n")

# --- SPLIT 2: SemanticChunker ---
print("\n🔸 Splitting with SemanticChunker (OpenAI embeddings)")
embedding = OpenAIEmbeddings(model="text-embedding-3-small")
semantic_splitter = SemanticChunker(embedding)
semantic_chunks = semantic_splitter.split_documents(documents)
print(f"🔸 Semantic: {len(semantic_chunks)} chunks")

for i, chunk in enumerate(semantic_chunks[:2]):
    print(f"\n🧠 Semantic Chunk {i+1}:\n{chunk.page_content[:300]}...\n")

# --- Cleanup ---
os.remove(tmp_path)
