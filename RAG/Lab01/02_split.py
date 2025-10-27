from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

# Specify the path to your PDF
pdf_path = "2312_10997v5.pdf"

# Initialize the PDF loader
loader = PyPDFLoader("2312_10997v5.pdf")

# Load the PDF
documents = loader.load()

# --- SPLIT 1: RecursiveCharacterTextSplitter ---
print("\n🔹 Splitting using RecursiveCharacterTextSplitter")
recursive_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
recursive_chunks = recursive_splitter.split_documents(documents)
print(f"🔹 Recursive: {len(recursive_chunks)} chunks")

# Show first 2 recursive chunks
for i, chunk in enumerate(recursive_chunks[:2]):
    print(f"\n🧩 Recursive Chunk {i+1}:\n{chunk.page_content[:300]}...\n")

# --- SPLIT 2: SemanticChunker ---
print("\n🔸 Splitting using SemanticChunker (with OpenAI Embeddings)")

embedding = OpenAIEmbeddings(model="text-embedding-3-small")  # Uses OPENAI_API_KEY
semantic_splitter = SemanticChunker(embedding)
semantic_chunks = semantic_splitter.split_documents(documents)
print(f"🔸 Semantic: {len(semantic_chunks)} chunks")

# Show first 2 semantic chunks
for i, chunk in enumerate(semantic_chunks[:2]):
    print(f"\n🧠 Semantic Chunk {i+1}:\n{chunk.page_content[:300]}...\n")