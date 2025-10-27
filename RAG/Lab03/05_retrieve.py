from genie.testbed import load
from langchain_community.document_loaders import JSONLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
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
# --- Step 3: Load JSON into LangChain Documents ---
loader = JSONLoader(
    file_path=tmp_path,
    jq_schema='.',              # Entire JSON object (one doc per interface)
    text_content=False
)

documents = loader.load()
os.remove(tmp_path)

# --- Step 4: Embed & Split ---
embedding = OpenAIEmbeddings(model="text-embedding-3-small")
semantic_splitter = SemanticChunker(embedding)
semantic_chunks = semantic_splitter.split_documents(documents)

# --- Step 5: Store in Chroma ---
session_id = str(uuid.uuid4())
persist_path = f"chroma_routes_{session_id}"

vector_store = Chroma.from_documents(
    semantic_chunks,
    embedding,
    persist_directory=persist_path
)
vector_store.persist()
print("📦 Chroma vector store ready and persisted.")

# --- Method 1: Direct semantic search ---
print("\n🔎 Method 1: Direct similarity search")
questions = [
    "What is the next hop for 192.168.1.0/24?",
    "Which prefixes are connected interfaces?",
    "Is there a static route for 10.1.1.0/24?",
    "Do I have a default route?",
]

for q in questions:
    print(f"\n❓ Q: {q}")
    results = vector_store.similarity_search(q, k=2)
    for i, doc in enumerate(results):
        print(f"\n📄 Match {i+1}:\n{doc.page_content[:300]}...\n")

# --- Method 2: Conversational Retrieval QA ---
print("\n🤖 Method 2: Conversational RAG over routing data")

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True
)

chat_history = []
q2 = "Help me understand my routing table for R1?"
response = qa_chain.invoke({"question": q2, "chat_history": chat_history})

print(f"\n🧠 Answer: {response['answer']}\n")
print(f"📚 Source snippet:\n{response['source_documents'][0].page_content[:300]}...\n")
