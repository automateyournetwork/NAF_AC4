from langchain_community.document_loaders import PyPDFLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import uuid

# Specify the path to your PDF
pdf_path = "2312_10997v5.pdf"

# Initialize the PDF loader
loader = PyPDFLoader("2312_10997v5.pdf")

# Load the PDF
documents = loader.load()

embedding = OpenAIEmbeddings(model="text-embedding-3-small")  # Uses OPENAI_API_KEY
semantic_splitter = SemanticChunker(embedding)
semantic_chunks = semantic_splitter.split_documents(documents)

print(f"🧠 Total chunks created: {len(semantic_chunks)}")

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
persist_path = f"chroma_store_{session_id}"

persistent_db = Chroma.from_documents(
    semantic_chunks,
    embedding,
    persist_directory=persist_path
)

print(f"📁 Persistent Chroma DB saved to: {persist_path}")

# Explore persistent contents
raw_persist_data = persistent_db._collection.get()
print(f"📊 Persistent: {len(raw_persist_data['documents'])} documents")
print(f"🆔 Sample IDs: {raw_persist_data['ids'][:2]}")
print(f"📄 First Document Snippet:\n{raw_persist_data['documents'][0][:300]}...\n")
