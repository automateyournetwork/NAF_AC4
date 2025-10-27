from langchain_community.document_loaders import PyPDFLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Specify the path to your PDF
pdf_path = "2312_10997v5.pdf"

# Initialize the PDF loader
loader = PyPDFLoader("2312_10997v5.pdf")

# Load the PDF
documents = loader.load()

embedding = OpenAIEmbeddings(model="text-embedding-3-small")  # Uses OPENAI_API_KEY
semantic_splitter = SemanticChunker(embedding)
semantic_chunks = semantic_splitter.split_documents(documents)

# --- STEP 1: Hello World Embedding ---
hello_embedding = embedding.embed_query("Hello world!")

print("✅ 'Hello world!' embedding (first 5 dims):")
print(hello_embedding[:5])
print(f"🔢 Embedding length: {len(hello_embedding)}\n")

# --- STEP 2: Compare Embeddings ---
print("📏 Comparing similar sentences...")

text_1 = "Neural networks for language modeling"
text_2 = "Deep learning for natural language processing"

embed_1 = embedding.embed_query(text_1)
embed_2 = embedding.embed_query(text_2)

similarity = cosine_similarity([embed_1], [embed_2])[0][0]

print(f"🧠 Cosine similarity between:\n- '{text_1}'\n- '{text_2}'\n→ {similarity:.4f}\n")

# --- STEP 3: Show first chunk embedding ---
print("📘 Embedding first semantic chunk from the PDF...")

first_chunk_text = semantic_chunks[0].page_content
first_chunk_vector = embedding.embed_query(first_chunk_text)

print(f"🔢 First PDF chunk embedding (first 5 dims): {first_chunk_vector[:5]}")
print(f"📄 Preview of text:\n{first_chunk_text[:300]}...\n")