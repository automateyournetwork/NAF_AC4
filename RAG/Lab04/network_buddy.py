import streamlit as st
from genie.testbed import load
from langchain_community.document_loaders import JSONLoader, TextLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from openai import OpenAI
import json, os, tempfile, re

# -------------------------------------------------
# JSON Extraction Helper (handles code fences, etc.)
# -------------------------------------------------
def extract_json(text: str):
    """
    Extracts the first valid JSON object from a string.
    Handles:
    - code fences ```json ... ```
    - extra whitespace
    - text before/after the JSON
    - stray newlines
    """
    # Remove ```json or ``` wrappers
    text = text.replace("```json", "")
    text = text.replace("```", "")

    # Extract first {...} block
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError(f"No JSON object found in: {text}")

    json_str = match.group(0)

    try:
        return json.loads(json_str)
    except Exception as e:
        raise ValueError(f"Invalid JSON extracted: {json_str}\nError: {e}")

# -------------------------------------------------
# Smart Parse / Execute Helper for pyATS
# -------------------------------------------------
def smart_run(device, command):
    """
    Try pyATS parser first unless running 'show run' or 'show running-config'.
    Force raw output for running-config.
    """
    from genie.metaparser.util.exceptions import SchemaEmptyParserError, SchemaMissingKeyError

    # ---- FORCE RAW MODE FOR RUNNING CONFIG ----
    if "show run" in command or "show running" in command:
        raw_output = device.execute(command)
        return raw_output, True

    # ---- TRY PARSED MODE FOR OTHER COMMANDS ----
    try:
        parsed = device.parse(command)
        return parsed, False

    except (SchemaEmptyParserError, SchemaMissingKeyError):
        return device.execute(command), True

    except Exception:
        return device.execute(command), True

# -------------------------------------------------
# Streamlit UI Setup
# -------------------------------------------------
st.set_page_config(page_title="🤖 Network Buddy", page_icon="🛠️")
st.title("🤖 Network Buddy")
st.markdown("Ask anything about your live network — routes, interfaces, configs, protocols!")

# -------------------------------------------------
# Load Testbed + Device Names
# -------------------------------------------------
try:
    testbed = load("testbed.yaml")
    DEVICE_LIST = list(testbed.devices.keys())
    DEVICE_STRING = ", ".join(DEVICE_LIST)
except Exception as e:
    st.error(f"❌ Failed to load testbed.yaml: {e}")
    st.stop()

# -------------------------------------------------
# Planner Prompt
# -------------------------------------------------
PLANNER_SYSTEM_PROMPT = f"""
You are a Cisco network assistant.

Only choose device names from this list:
{DEVICE_STRING}

Given a user's question, output ONLY a JSON object in EXACTLY this format:

{{
  "device": "<one of: {DEVICE_STRING}>",
  "command": "<a valid Cisco IOS XE show command>",
  "intent": "<why this command answers the question>"
}}

RULES:
- Never invent or modify a device name.
- If the user asks for a non-existent device, ask for clarification.
- ONLY return valid strict JSON.
- No explanations, no backticks, no code fences.
"""

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------------------------------
# UI Input
# -------------------------------------------------
user_question = st.text_input("💬 What do you want to know? (e.g., 'What is the default route on Cat9k_AO_Sandbox?')")

# -------------------------------------------------
# Main Logic
# -------------------------------------------------
if user_question:

    # ---- PLANNER ----------------------------------------------------------
    with st.spinner("🤔 Planning next action..."):
        raw_plan = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": user_question}
            ]
        ).choices[0].message.content

    # ---- SAFE JSON EXTRACTION --------------------------------------------
    try:
        plan = extract_json(raw_plan)
    except Exception as e:
        st.error(f"❌ LLM did not return valid JSON.\n\nReturned:\n{raw_plan}\n\nError: {e}")
        st.stop()

    # ---- VALIDATE DEVICE --------------------------------------------------
    if plan["device"] not in DEVICE_LIST:
        st.error(f"❌ Device '{plan['device']}' not found.\nValid devices: {DEVICE_STRING}")
        st.stop()

    st.success(f"📡 Running `{plan['command']}` on `{plan['device']}` — {plan['intent']}")

    # ---- EXECUTION (parse or fallback) -----------------------------------
    try:
        device = testbed.devices[plan["device"]]
        device.connect(log_stdout=True, timeout=30)

        output, is_raw = smart_run(device, plan["command"])
    except Exception as e:
        st.error(f"❌ Could not connect or run command: {e}")
        st.stop()

    # ---- SAVE TEMP FILE (RAW OR JSON) -----------------------------------
    suffix = ".txt" if is_raw else ".json"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode="w") as tmp:
        if is_raw:
            tmp.write(output)
        else:
            json.dump(output, tmp, indent=2)
        tmp_path = tmp.name

    # ---- LOAD FOR RAG -----------------------------------------------------
    loader = TextLoader(tmp_path) if is_raw else JSONLoader(tmp_path, jq_schema=".", text_content=False)
    documents = loader.load()
    os.remove(tmp_path)

    # ---- CHUNK + EMBED ----------------------------------------------------
    embedding = OpenAIEmbeddings(model="text-embedding-3-small")
    splitter = SemanticChunker(embedding)
    chunks = splitter.split_documents(documents)

    vectorstore = Chroma.from_documents(chunks, embedding)

    # ---- RAG QA -----------------------------------------------------------
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    qa = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
        return_source_documents=True
    )

    with st.spinner("💡 Generating answer..."):
        response = qa.invoke({"question": user_question, "chat_history": []})

    # ---- DISPLAY RESULTS --------------------------------------------------
    st.markdown(f"### 🤖 Network Buddy Answer\n{response['answer']}")

    with st.expander("📄 Source Snippet"):
        if response["source_documents"]:
            st.code(response["source_documents"][0].page_content[:1500])
        else:
            st.write("No source documents available.")
