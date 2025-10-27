from genie.testbed import load
from langchain_community.document_loaders import JSONLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from sklearn.metrics.pairwise import cosine_similarity
import tempfile
import json
import os

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

# --- Step 4: Embed & Split ---
embedding = OpenAIEmbeddings(model="text-embedding-3-small")
semantic_splitter = SemanticChunker(embedding)
semantic_chunks = semantic_splitter.split_documents(documents)

print(f"\n📄 Parsed {len(documents)} documents → {len(semantic_chunks)} semantic chunks")

# --- STEP 5: Hello World Embedding ---
hello_embedding = embedding.embed_query("Hello world!")
print("✅ 'Hello world!' embedding (first 5 dims):")
print(hello_embedding[:5])
print(f"🔢 Embedding length: {len(hello_embedding)}\n")

# --- STEP 6: Compare Route-Related Embeddings ---
print("📏 Comparing similar route phrases...")

text_1 = "static route to 192.168.1.0/24 via 10.1.1.1"
text_2 = "default route through next-hop 10.1.1.1 interface GigabitEthernet1"

embed_1 = embedding.embed_query(text_1)
embed_2 = embedding.embed_query(text_2)

similarity = cosine_similarity([embed_1], [embed_2])[0][0]
print(f"🧠 Cosine similarity between:\n- '{text_1}'\n- '{text_2}'\n→ {similarity:.4f}\n")

# --- STEP 7: Embed First Routing Chunk ---
print("📘 Embedding first routing chunk...")

first_chunk_text = semantic_chunks[0].page_content
first_chunk_vector = embedding.embed_query(first_chunk_text)

print(f"🔢 First route chunk embedding (first 5 dims): {first_chunk_vector[:5]}")
print(f"📄 Preview of text:\n{first_chunk_text[:300]}...\n")

# --- Clean up ---
os.remove(tmp_path)
