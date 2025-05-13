# DeloitteSmart™ AI Assistant – Full Version (Enhanced Multi-Doc Summarizer, Camera OCR, Persistent Chat, Feedback, Downloadable Report)

import streamlit as st
import openai
import fitz  # PyMuPDF
import json
from datetime import datetime
from openai import OpenAIError
import os
from io import BytesIO
import base64

# --- CONFIG ---
st.set_page_config(
    page_title="DeloitteSmart™ - AI Assistant",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LANGUAGE TOGGLE ---
language = st.sidebar.radio("🌐 Language / 言語", ["English", "日本語"], index=0)

def t(en_text, jp_text):
    return en_text if language == "English" else jp_text

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
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
init_session()

# --- MODE & CAMERA ---
st.markdown("### Mode Selection and Camera Toggle")
col1, col2 = st.columns([3, 1])
with col1:
    st.session_state.selected_mode = st.radio("Choose interaction mode:", ["Client-Asks (Default)", "Deloitte-Asks"], index=0)
with col2:
    enable_camera = st.checkbox("📸 Enable Camera", value=False)

st.title("DeloitteSmart™: Your AI Assistant for Faster, Smarter Decisions")

# --- FILE UPLOAD ---
with st.expander("📁 Upload Documents (PDF, TXT)"):
    uploaded_files = st.file_uploader("Upload Files", type=["pdf", "txt"], accept_multiple_files=True)
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

# --- CAMERA CAPTURE ---
if enable_camera:
    st.subheader("📸 Capture Image for Testing")
    image = st.camera_input("Take a picture")
    if image:
        st.image(image)
        doc_id = f"CameraCapture_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        st.session_state.document_content[doc_id] = "Demo photo uploaded. In full version, OCR will extract and summarize."
        st.session_state.document_summary[doc_id] = "**Demo Summary**: This is a placeholder.\n**Questions:** 1. What is the image about? 2. Who is it for?"
        st.session_state.uploaded_filenames.append(doc_id)

# --- DISPLAY SUMMARIES ---
if st.session_state.document_summary:
    st.subheader("📄 Summaries & Smart Questions")
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
            except OpenAIError as e:
                st.error(f"OpenAI Error: {str(e)}")

# --- DELOITTE-ASKS MODE ---
elif st.session_state.selected_mode == "Deloitte-Asks":
    st.subheader(t("Get Smart Questions to Ask Your Client", "クライアントに尋ねるスマートな質問を取得"))
    client_profile = st.text_area(t("Describe the client (industry, size, goal, etc.)", "クライアントを説明してください（業種、規模、目標など）:"), key="client_profile")
    uploaded_file = st.file_uploader(t("Upload Client Business Overview (Optional - .txt file)", "クライアントのビジネス概要をアップロード（オプション - .txtファイル）"), type=["txt"], key="client_doc")

    document_content = uploaded_file.read().decode("utf-8") if uploaded_file else "No document provided."

    if st.button(t("Get AI Insights & Questions", "AIの洞察と質問を取得")):
        if not openai_api_key:
            st.error("API key missing.")
        elif not client_profile.strip():
            st.warning("Please describe the client first.")
        else:
            try:
                prompt = f"You are an AI assistant analyzing client profiles and business plans to recommend subsidy programs and suggest follow-up questions.\n\nClient Profile:\n{client_profile}\n\nClient Document:\n{document_content}\n\nBased on this, please suggest:\n1. One or two likely suitable Japanese subsidy programs.\n2. Two to three intelligent follow-up questions."
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a Deloitte subsidy expert."},
                        {"role": "user", "content": prompt}
                    ]
                )
                ai_response = response.choices[0].message.content
                st.markdown("### AI Insights & Recommendations")
                st.markdown(ai_response)
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
