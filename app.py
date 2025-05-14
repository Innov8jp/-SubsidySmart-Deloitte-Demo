
# DeloitteSmart™ AI Assistant – Enhanced Version (Multi-Doc, Persistent Chat, Feedback, Camera Demo, Japanese Toggle Fix)

import streamlit as st
import openai
import fitz  # PyMuPDF
import json
from datetime import datetime
from openai import OpenAIError
import os
from io import BytesIO
import base64
from PIL import Image

# --- CONFIG ---
st.set_page_config(
    page_title="DeloitteSmart™ - AI Assistant",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LANGUAGE TOGGLE ---
if "language" not in st.session_state:
    st.session_state.language = "English"
language = st.sidebar.radio("🌐 Language / 言語", ["English", "日本語"], index=0)
st.session_state.language = language

def t(en_text, jp_text):
    return en_text if st.session_state.language == "English" else jp_text

# --- SIDEBAR ---
st.sidebar.image("deloitte_logo.png", width=200)
openai_api_key = st.secrets.get("OPENAI_API_KEY")
if openai_api_key:
    st.sidebar.success("✅ OpenAI API key is pre-configured.")
else:
    st.sidebar.error("❌ OpenAI API key not found.")
st.sidebar.markdown("Powered by [Innov8]")
st.sidebar.markdown("Prototype Version 1.0")
st.sidebar.markdown("Secure | Scalable | Smart")

# --- SESSION STATE ---
def init_session():
    defaults = {
        "chat_history": [],
        "document_content": {},
        "document_summary": {},
        "uploaded_filenames": [],
        "selected_mode": "Client-Asks (Default)",
        "feedback_entries": []
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
init_session()

# --- MODE & CAMERA ---
st.markdown("### Mode Selection and Camera Toggle")
col1, col2 = st.columns([3, 1])
with col1:
    st.session_state.selected_mode = st.radio(
        "Choose interaction mode:",
        ["Client-Asks (Default)", "Deloitte-Asks"],
        index=0
    )
with col2:
    enable_camera = st.checkbox("📸 Enable Camera", value=False)

st.title(
    t(
        "DeloitteSmart™: Your AI Assistant for Faster, Smarter Decisions",
        "DeloitteSmart™: よりスマートな意思決定のためのAIアシスタント"
    )
)

if enable_camera:
    st.header("📸 Document Capture & OCR")
    tab_front, tab_rear = st.tabs(["Front Camera", "Rear Camera"])
    with tab_front:
        img_front = st.camera_input("Capture using front camera")
    with tab_rear:
        img_rear = st.file_uploader(
            "Capture/upload rear-camera image",
            type=["png", "jpg", "jpeg"]
        )
    img_file = img_front or img_rear

    if img_file:
        st.image(img_file, use_column_width=True)
        img_bytes = img_file.getvalue() if hasattr(img_file, "getvalue") else img_file.read()
        with st.spinner("Extracting text…"):
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": "Please extract all the text from this document image."
                }],
                files=[{"filename": "doc.jpg", "data": img_bytes}]
          st.subheader("📝 Extracted Text")
st.text_area("", resp.choices[0].message.content, height=300)

st.title(
    t(
        "DeloitteSmart™: Your AI Assistant for Faster, Smarter Decisions",
        "DeloitteSmart™: よりスマートな意思決定のためのAIアシスタント"
    )
)
if enable_camera:
    st.header("📸 Document Capture & OCR")
    # Front vs. Rear camera tabs
    tab_front, tab_rear = st.tabs(["Front Camera", "Rear Camera"])
    with tab_front:
        img_front = st.camera_input("Capture using front camera")
    with tab_rear:
        img_rear = st.file_uploader(
            "Capture/upload rear-camera image",
            type=["png", "jpg", "jpeg"]
        )
    img_file = img_front or img_rear

    if img_file:
        st.image(img_file, use_column_width=True)
        img_bytes = (
            img_file.getvalue()
            if hasattr(img_file, "getvalue")
            else img_file.read()
        )
        with st.spinner("Extracting text…"):
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": "Please extract all the text from this document image."
                }],
                files=[{"filename": "doc.jpg", "data": img_bytes}]
            )
        st.subheader("📝 Extracted Text")
        st.text_area("", resp.choices[0].message.content, height=300)

# --- FILE UPLOAD ---
with st.expander(t("📁 Upload Documents (PDF, TXT)", "📁 ドキュメントをアップロード")):
    uploaded_files = st.file_uploader(t("Upload Files", "ファイルをアップロード"), type=["pdf", "txt"], accept_multiple_files=True)
    if uploaded_files:
        for file in uploaded_files:
            filename = file.name
            if filename not in st.session_state.uploaded_filenames:
                file_text = ""
                try:
                    if file.type == "application/pdf":
                        with fitz.open(stream=file.read(), filetype="pdf") as doc:
                            for page in doc:
                                file_text += page.get_text()
                    elif file.type == "text/plain":
                        file_text = file.read().decode("utf-8")
                except Exception as e:
                    st.error(f"Failed to read {filename}: {e}")
                    continue
                st.session_state.document_content[filename] = file_text
                st.session_state.uploaded_filenames.append(filename)

                if openai_api_key:
                    try:
                        prompt = f"You are a consultant. Summarize and generate 5 questions.\n\nDocument:\n{file_text}"
                        response = openai.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are a helpful AI assistant."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        st.session_state.document_summary[filename] = response.choices[0].message.content
                    except Exception as e:
                        st.error(f"Error summarizing {filename}: {e}")

# --- DISPLAY SUMMARIES ---
if st.session_state.document_summary:
    st.subheader(t("📄 Summaries & Smart Questions", "📄 要約とスマートな質問"))
    for fname, summary in st.session_state.document_summary.items():
        st.markdown(f"**🗂️ {fname}**")
        st.markdown(summary)
        st.markdown("---")

# --- CLIENT-ASKS MODE ---
if st.session_state.selected_mode == "Client-Asks (Default)":
    st.subheader(t("Ask Your Question", "質問してください"))
    with st.form("chat_input_form", clear_on_submit=True):
        col1, col2 = st.columns([9, 1])
        with col1:
            user_input = st.text_input(t("Ask anything about the uploaded documents...", "アップロードされたドキュメントについて質問してください..."), key="user_input")
        with col2:
            st.markdown("<div>&nbsp;</div>", unsafe_allow_html=True)
            submitted = st.form_submit_button(t("Ask", "質問する"), use_container_width=True)

    if submitted and user_input:
        all_text = "\n\n".join(st.session_state.document_content.values())
        if not all_text.strip():
            st.warning("Please upload documents before asking questions.")
        elif not openai_api_key:
            st.warning("OpenAI API key is not configured.")
        else:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            try:
                prompt = f"You are an AI agent. Answer the question using the following documents.\n\nDocuments:\n{all_text}\n\nQuestion: {user_input}"
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a document-savvy AI assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
                answer = response.choices[0].message.content
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                st.success("✅ Answer generated!")
                st.markdown(answer)

                # --- WAS THIS HELPFUL ---
                st.write("**Was this helpful?**")
                col_yes, col_no = st.columns([1, 1])
                with col_yes:
                    if st.button("👍 Yes", key=f"yes_{len(st.session_state.chat_history)}"):
                        st.session_state.feedback_entries.append({
                            "index": len(st.session_state.chat_history) - 1,
                            "helpful": True,
                            "timestamp": datetime.now().isoformat()
                        })
                        st.success("Thanks for your feedback!")
                with col_no:
                    if st.button("👎 No", key=f"no_{len(st.session_state.chat_history)}"):
                        st.session_state.feedback_entries.append({
                            "index": len(st.session_state.chat_history) - 1,
                            "helpful": False,
                            "timestamp": datetime.now().isoformat()
                        })
                        st.info("Feedback recorded. We'll improve from here.")
            except OpenAIError as e:
                st.error(f"OpenAI Error: {str(e)}")

# --- CHAT HISTORY ---
if st.session_state.chat_history:
    st.subheader("💬 Chat History")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(f"**{msg['role'].capitalize()}:** {msg['content']}")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔁 Reset Chat"):
            st.session_state.chat_history = []
            st.success("Chat history cleared.")
    with col2:
        st.download_button("📅 Download Chat History", data=json.dumps(st.session_state.chat_history, indent=2), file_name="chat_history.json", mime="application/json")

# --- FEEDBACK REVIEW ---
if st.session_state.feedback_entries:
    st.subheader("📬 Submitted Feedback")
    for fb in st.session_state.feedback_entries:
        st.markdown(f"- Chat #{fb['index'] + 1} — {'👍 Helpful' if fb['helpful'] else '👎 Not Helpful'} @ {fb['timestamp']}")
