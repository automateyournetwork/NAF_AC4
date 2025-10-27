import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
import tempfile
import os

st.set_page_config(page_title="📄 Chat with Your PDF", page_icon="📎")
st.title("📄 Chat with Your PDF")
st.markdown("Upload a PDF and ask it questions using RAG!")

# --- PDF Upload ---
uploaded_file = st.file_uploader("📎 Upload a PDF", type=["pdf"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    st.success("✅ PDF uploaded successfully!")

    # --- Load & Chunk ---
    with st.spinner("🔍 Loading and embedding your document..."):
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()

        embedding = OpenAIEmbeddings(model="text-embedding-3-small")
        splitter = SemanticChunker(embedding)
        chunks = splitter.split_documents(documents)

        vector_store = Chroma.from_documents(chunks, embedding)
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})

        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            return_source_documents=True
        )

    # --- Initialize Chat History ---
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # --- Chat UI ---
    question = st.text_input("💬 Ask something about your PDF")

    if question:
        with st.spinner("Thinking..."):
            response = qa_chain.invoke({
                "question": question,
                "chat_history": st.session_state.chat_history
            })
            st.session_state.chat_history.append((question, response["answer"]))

    # --- Display Chat ---
    for user_q, answer in reversed(st.session_state.chat_history):
        st.markdown(f"**🧑‍💻 You:** {user_q}")
        st.markdown(f"**🤖 RAGBot:** {answer}")
        st.markdown("---")

    # --- Clean up temp file ---
    os.remove(tmp_path)
else:
    st.info("👆 Upload a PDF to begin.")
