import streamlit as st
from genie.testbed import load
from langchain_community.document_loaders import JSONLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
import json, os, tempfile, uuid
from openai import OpenAI

st.set_page_config(page_title="🤖 Network Buddy", page_icon="🛠️")
st.title("🤖 Network Buddy")
st.markdown("Ask anything about your live network — routes, interfaces, protocols!")

# --- Let user ask a question ---
user_question = st.text_input("💬 What do you want to know? (e.g., 'What is the default route on R1?')")

# --- LLM Prompt for Planning ---
PLANNER_SYSTEM_PROMPT = """
You are a Cisco network assistant. Given a user's question, output a JSON object:

{
  "device": "<device name from testbed.yaml>",
  "command": "<Cisco IOS XE show command>",
  "intent": "<brief description of why this command is relevant>"
}

If unsure, ask for clarification.
"""

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- On user submit ---
if user_question:
    with st.spinner("🤔 Thinking about what to do..."):
        plan_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": user_question}
            ]
        )

        plan = json.loads(plan_response.choices[0].message.content)

        st.success(f"📡 Running `{plan['command']}` on `{plan['device']}` — {plan['intent']}")

        # --- pyATS Command Execution ---
        try:
            testbed = load("testbed.yaml")
            device = testbed.devices[plan["device"]]
            device.connect(log_stdout=True, timeout=30)
            parsed_output = device.parse(plan["command"])
        except Exception as e:
            st.error(f"❌ Could not connect or parse: {e}")
            st.stop()

        # --- Save and Load as LangChain Documents ---
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w") as tmp:
            json.dump(parsed_output, tmp, indent=2)
            tmp_path = tmp.name

        loader = JSONLoader(
            file_path=tmp_path,
            jq_schema='.',
            text_content=False
        )
        documents = loader.load()
        os.remove(tmp_path)

        # --- Chunk + Embed ---
        embedding = OpenAIEmbeddings(model="text-embedding-3-small")
        splitter = SemanticChunker(embedding)
        chunks = splitter.split_documents(documents)
        vectorstore = Chroma.from_documents(chunks, embedding)

        # --- RAG QA ---
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        qa = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
            return_source_documents=True
        )

        with st.spinner("💡 Generating answer..."):
            response = qa.invoke({"question": user_question, "chat_history": []})
            st.markdown(f"**🤖 Network Buddy:** {response['answer']}")
            with st.expander("📄 Source Snippet"):
                st.code(response['source_documents'][0].page_content[:1000])
