import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain

# --- Load + Embed + Index (cache this to avoid reloading every time) ---
@st.cache_resource
def setup_rag_chain():
    loader = PyPDFLoader("2312_10997v5.pdf")
    documents = loader.load()

    embedding = OpenAIEmbeddings(model="text-embedding-3-small")
    splitter = SemanticChunker(embedding)
    chunks = splitter.split_documents(documents)

    vector_store = Chroma.from_documents(chunks, embedding)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    qa = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )
    return qa

# --- Streamlit UI ---
st.set_page_config(page_title="Ask the RAG Paper", page_icon="📄")
st.title("📄 Ask the RAG Paper")
st.markdown("Type your question below to explore the Retrieval-Augmented Generation for Large Language Models Survey")

qa_chain = setup_rag_chain()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

question = st.text_input("💬 Your question:", placeholder="e.g. What is RAG?")

if question:
    with st.spinner("Thinking..."):
        response = qa_chain.invoke({
            "question": question,
            "chat_history": st.session_state.chat_history
        })
        st.session_state.chat_history.append((question, response["answer"]))

# --- Display chat history ---
for user_q, answer in reversed(st.session_state.chat_history):
    st.markdown(f"**🧑‍💻 You:** {user_q}")
    st.markdown(f"**🤖 RAGBot:** {answer}")
    st.markdown("---")
