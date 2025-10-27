from langchain_community.document_loaders import PyPDFLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
import uuid

# --- Load & Embed ---
print("📄 Loading and embedding the RAG paper...")
loader = PyPDFLoader("2312_10997v5.pdf")
documents = loader.load()

embedding = OpenAIEmbeddings(model="text-embedding-3-small")
splitter = SemanticChunker(embedding)
chunks = splitter.split_documents(documents)

print(f"🧠 Total chunks: {len(chunks)}")

# --- Store in Chroma (in memory) ---
vector_store = Chroma.from_documents(chunks, embedding)
print("📥 Vector store ready.")

# --- Method 1: Basic semantic search ---
print("\n🔎 Method 1: Direct similarity search")
questions = [
    "What is retrieval-augmented generation?",
    "What is the purpose of the retriever?",
    "How do language models use context in RAG?"
]

for q in questions:
    print(f"\n❓ Q: {q}")
    results = vector_store.similarity_search(q, k=2)
    for i, doc in enumerate(results):
        print(f"\n📄 Match {i+1}:\n{doc.page_content[:300]}...\n")

# --- Method 2: RAG-style QA with ConversationalRetrievalChain ---
print("\n🤖 Method 2: RAG-style conversational retrieval")

# Setup
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True
)

chat_history = []
q2 = "What are the components of a RAG system?"
response = qa_chain.invoke({"question": q2, "chat_history": chat_history})

print(f"\n🧠 Answer: {response['answer']}\n")
print(f"📚 Source snippet:\n{response['source_documents'][0].page_content[:300]}...")