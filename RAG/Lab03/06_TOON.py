import os
import json
import uuid
import tempfile
import subprocess

from genie.testbed import load
from langchain_community.document_loaders import TextLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain

import tiktoken
from typing import Any

# ================================================================
# TOKENIZER
# ================================================================
try:
    tokenizer = tiktoken.get_encoding("o200k_base")
except Exception:
    tokenizer = None

def count_tokens(text: str) -> int:
    if tokenizer is None:
        return -1
    try:
        return len(tokenizer.encode(text))
    except Exception:
        return -1


# ================================================================
# SAFE JSON NORMALIZATION
# ================================================================
def make_json_safe(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [make_json_safe(v) for v in obj]
    if isinstance(obj, set):
        return sorted([make_json_safe(v) for v in obj], key=lambda x: str(x))
    if hasattr(obj, "__dict__"):
        return make_json_safe(obj.__dict__)
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return str(obj)


# ================================================================
# TOON CONVERSION
# ================================================================
def toon_with_stats(pyats_json: Any) -> tuple[str, str]:
    """
    Returns:
      toon_text (str)
      stats_report (str)
    """
    safe = make_json_safe(pyats_json)
    json_str = json.dumps(safe, indent=2)

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as f_json:
        f_json.write(json_str)
        f_json.flush()
        src = f_json.name
        dst = f_json.name + ".toon"

    # run npx
    cmd = ["npx", "@toon-format/cli", src, "-o", dst]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"TOON CLI failed:\n{result.stderr}")

    toon_text = open(dst).read()

    # token savings
    j_tokens = count_tokens(json_str)
    t_tokens = count_tokens(toon_text)

    if j_tokens > 0 and t_tokens > 0:
        reduction = 100 * (1 - (t_tokens / j_tokens))
        stats = (
            "=== TOKEN SAVINGS ===\n"
            f"JSON tokens: {j_tokens}\n"
            f"TOON tokens: {t_tokens}\n"
            f"Saved: {reduction:.1f}%\n"
        )
    else:
        stats = "=== TOKEN SAVINGS ===\n(unavailable)\n"

    return toon_text, stats


# ================================================================
# MAIN PIPELINE
# ================================================================
# Step 1: Connect to device and parse pyATS JSON
testbed = load("testbed.yaml")
device = testbed.devices["Cat9k_AO_Sandbox"]
device.connect(log_stdout=True)

pyats_parsed = device.parse("show interfaces")

# Step 2: Convert to TOON
toon_text, stats = toon_with_stats(pyats_parsed)

print("\n============================")
print("📦 TOON OUTPUT PREVIEW")
print("============================\n")
print(toon_text[:500], "...\n")

print("----------------------------")
print(stats)
print("----------------------------\n")

# Step 3: Put TOON text into a temp file so LangChain can load it
with tempfile.NamedTemporaryFile(delete=False, suffix=".toon", mode="w") as tmp:
    tmp.write(toon_text)
    tmp_path = tmp.name

# Step 4: Load TOON as a single text document
loader = TextLoader(tmp_path)
documents = loader.load()
os.remove(tmp_path)

# Step 5: Embed & semantic split
embedding = OpenAIEmbeddings(model="text-embedding-3-small")
splitter = SemanticChunker(embedding)
chunks = splitter.split_documents(documents)

# Step 6: Chroma vector store
session_id = str(uuid.uuid4())
persist_path = f"chroma_toon_{session_id}"

vector_store = Chroma.from_documents(
    chunks,
    embedding,
    persist_directory=persist_path
)
vector_store.persist()

print("📦 Chroma vector store (TOON-based) ready.\n")

# Step 7: Conversational Retrieval QA
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True
)

chat_history = []
question = "Provide a summary of all my interfaces."
response = qa_chain.invoke({"question": question, "chat_history": chat_history})

print("🧠 LLM Answer:\n", response["answer"])
print("\n📚 Source Snippet:\n", response["source_documents"][0].page_content[:300])

pyats_parsed = device.parse("show ip interface brief")

# Step 2: Convert to TOON
toon_text, stats = toon_with_stats(pyats_parsed)

print("\n============================")
print("📦 TOON OUTPUT PREVIEW")
print("============================\n")
print(toon_text[:500], "...\n")

print("----------------------------")
print(stats)
print("----------------------------\n")

# Step 3: Put TOON text into a temp file so LangChain can load it
with tempfile.NamedTemporaryFile(delete=False, suffix=".toon", mode="w") as tmp:
    tmp.write(toon_text)
    tmp_path = tmp.name

# Step 4: Load TOON as a single text document
loader = TextLoader(tmp_path)
documents = loader.load()
os.remove(tmp_path)

# Step 5: Embed & semantic split
embedding = OpenAIEmbeddings(model="text-embedding-3-small")
splitter = SemanticChunker(embedding)
chunks = splitter.split_documents(documents)

# Step 6: Chroma vector store
session_id = str(uuid.uuid4())
persist_path = f"chroma_toon_{session_id}"

vector_store = Chroma.from_documents(
    chunks,
    embedding,
    persist_directory=persist_path
)
vector_store.persist()

print("📦 Chroma vector store (TOON-based) ready.\n")

# Step 7: Conversational Retrieval QA
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True
)

chat_history = []
question = "Provide a summary of all my interfaces."
response = qa_chain.invoke({"question": question, "chat_history": chat_history})

print("🧠 LLM Answer:\n", response["answer"])
print("\n📚 Source Snippet:\n", response["source_documents"][0].page_content[:300])

pyats_parsed = device.parse("show version")

# Step 2: Convert to TOON
toon_text, stats = toon_with_stats(pyats_parsed)

print("\n============================")
print("📦 TOON OUTPUT PREVIEW")
print("============================\n")
print(toon_text[:500], "...\n")

print("----------------------------")
print(stats)
print("----------------------------\n")

# Step 3: Put TOON text into a temp file so LangChain can load it
with tempfile.NamedTemporaryFile(delete=False, suffix=".toon", mode="w") as tmp:
    tmp.write(toon_text)
    tmp_path = tmp.name

# Step 4: Load TOON as a single text document
loader = TextLoader(tmp_path)
documents = loader.load()
os.remove(tmp_path)

# Step 5: Embed & semantic split
embedding = OpenAIEmbeddings(model="text-embedding-3-small")
splitter = SemanticChunker(embedding)
chunks = splitter.split_documents(documents)

# Step 6: Chroma vector store
session_id = str(uuid.uuid4())
persist_path = f"chroma_toon_{session_id}"

vector_store = Chroma.from_documents(
    chunks,
    embedding,
    persist_directory=persist_path
)
vector_store.persist()

print("📦 Chroma vector store (TOON-based) ready.\n")

# Step 7: Conversational Retrieval QA
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True
)

chat_history = []
question = "Provide a summary of all device IOS version."
response = qa_chain.invoke({"question": question, "chat_history": chat_history})

print("🧠 LLM Answer:\n", response["answer"])
print("\n📚 Source Snippet:\n", response["source_documents"][0].page_content[:300])
