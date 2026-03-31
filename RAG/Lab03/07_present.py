import streamlit as st
from genie.testbed import load
from langchain_community.document_loaders import JSONLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
import tempfile, os, json, uuid

# --- UI Setup ---
st.set_page_config(page_title="Chat with Cat9k_AO_Sandbox Interface Table", page_icon="🛣️")
st.title("🛣️ Chat with Your Cat9k_AO_Sandbox Interface Table")
st.markdown("Ask anything about the live Interface table retrieved from Cat9k_AO_Sandbox using pyATS!")

# --- Cached RAG Pipeline Setup ---
def setup_routing_chain():
    # Step 1: Connect to Cat9k_AO_Sandbox and get routing table
    testbed = load("testbed.yaml")
    device = testbed.devices["Cat9k_AO_Sandbox"]
    print("🔌 Connecting to Cat9k_AO_Sandbox...")
    device.connect(log_stdout=True)
    parsed_output = device.parse("show ip interface brief")

    # Step 2: Write JSON to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w") as tmp:
        json.dump(parsed_output, tmp, indent=2)
        tmp_path = tmp.name

    # Step 3: Load into LangChain Documents
    loader = JSONLoader(
        file_path=tmp_path,
        jq_schema='.',  # 1 route per document
        text_content=False
    )
    documents = loader.load()
    os.remove(tmp_path)

    # Step 4: Embed & Split
    embedding = OpenAIEmbeddings(model="text-embedding-3-small")
    splitter = SemanticChunker(embedding)
    chunks = splitter.split_documents(documents)

    # Step 5: Build Chroma vector store
    vector_store = Chroma.from_documents(chunks, embedding)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    # Step 6: Set up RAG chain
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )

    return qa_chain

qa_chain = setup_routing_chain()

# --- Chat Interaction ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

question = st.text_input("💬 Ask a question about Cat9k_AO_Sandbox's Interface table:")

if question:
    with st.spinner("Thinking..."):
        response = qa_chain.invoke({
            "question": question,
            "chat_history": st.session_state.chat_history
        })
        st.session_state.chat_history.append((question, response["answer"]))

# --- Display Chat History ---
for user_q, answer in reversed(st.session_state.chat_history):
    st.markdown(f"**🧑‍💻 You:** {user_q}")
    st.markdown(f"**🤖 Cat9k_AO_Sandbox Interface Bot:** {answer}")
    st.markdown("---")
