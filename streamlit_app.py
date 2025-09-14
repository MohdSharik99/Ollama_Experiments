import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000/api"  # Change if FastAPI runs elsewhere

st.set_page_config(page_title="DeepCoder Chat", page_icon="🤖", layout="wide")

# -------------------------------
# Session state
# -------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "doc_uploaded" not in st.session_state:
    st.session_state.doc_uploaded = False

# -------------------------------
# Sidebar for document upload
# -------------------------------
st.sidebar.header("📂 Upload Document")
uploaded_file = st.sidebar.file_uploader("Upload .txt, .docx, or .pdf", type=["txt", "docx", "pdf"])

if uploaded_file is not None:
    res = requests.post(
        f"{API_BASE}/upload",
        files={"file": (uploaded_file.name, uploaded_file, uploaded_file.type)},
    )
    if res.status_code == 200:
        st.sidebar.success(f"✅ {uploaded_file.name} uploaded")
        st.session_state.doc_uploaded = True
        st.session_state.messages = []  # reset history
    else:
        st.sidebar.error("❌ Upload failed")

# -------------------------------
# Chat UI
# -------------------------------
st.title("💬 DeepCoder Chatbot")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Type your question..."):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            # Streaming request to FastAPI
            with requests.post(f"{API_BASE}/chat", json={"prompt": prompt}, stream=True) as response:
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=None):
                    if chunk:
                        text = chunk.decode("utf-8")
                        full_response += text
                        message_placeholder.markdown(full_response + "▌")  # typing cursor effect

            message_placeholder.markdown(full_response)

        except Exception as e:
            full_response = f"⚠️ Error: {e}"
            message_placeholder.markdown(full_response)

        # Save assistant response
        st.session_state.messages.append({"role": "assistant", "content": full_response})
