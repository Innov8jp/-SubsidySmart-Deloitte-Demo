# DeloitteSmart™ AI Assistant – Enhanced UAT-Passed Version

import streamlit as st
import openai
import fitz  # PyMuPDF for PDF parsing
import json
from datetime import datetime
from openai import OpenAIError
import os
from io import BytesIO
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(
    page_title="DeloitteSmart™ - AI Assistant",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CREDENTIALS & INITIALIZATION ---
openai_api_key = st.secrets.get("OPENAI_API_KEY")
if not openai_api_key:
    st.sidebar.error("❌ OpenAI API key not found. Please configure it in Streamlit secrets.")
    st.stop()
openai.api_key = openai_api_key

# --- LANGUAGE TOGGLE ---
if "language" not in st.session_state:
    st.session_state.language = "English"
lang = st.sidebar.radio("🌐 Language / 言語", ["English", "日本語"], index=0)
st.session_state.language = lang

def t(en: str, jp: str) -> str:
    """Translation helper based on user's language toggle."""
    return en if st.session_state.language == "English" else jp

# --- SIDEBAR ---
st.sidebar.image("deloitte_logo.png", width=200)
st.sidebar.markdown("**Powered by Innov8**")
st.sidebar.markdown("Prototype Version 1.0 | Secure & Scalable")

# --- SESSION STATE SETUP ---
def init_session():
    defaults = {
        "chat_history": [],
        "document_content": {},
        "document_summary": {},
        "uploaded_filenames": [],
        "feedback_entries": []
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
init_session()

# --- MAIN TITLE ---
st.title(
    t(
        "DeloitteSmart™: Your AI Assistant for M&A and Document Insights",
        "DeloitteSmart™: M&A とドキュメント処理のための AI アシスタント"
    )
)

# --- CAMERA & OCR DEMO (Optional) ---
enable_camera = st.sidebar.checkbox(t("📸 Enable Camera OCR", "📸 カメラOCRを有効にする"), value=False)
if enable_camera:
    st.header(t("📸 Document Capture & OCR", "📸 ドキュメント撮影 & OCR"))
    st.markdown(
        t(
            "On mobile, use Rear Camera tab. On desktop, upload a photo.",
            "モバイルでは背面カメラタブを使用。デスクトップでは画像をアップロード。"
        )
    )
    front_tab, rear_tab = st.tabs([t("Front Camera", "前面カメラ"), t("Rear Camera", "背面カメラ")])
    with front_tab:
        img = st.camera_input(t("Capture front camera", "前面カメラで撮影"))
    with rear_tab:
        img = st.file_uploader(
            t("Upload image (rear camera)", "画像をアップロード（背面カメラ）"),
            type=["png", "jpg", "jpeg"]
        )
    if img:
        st.image(img, use_container_width=True)
        img_bytes = img.getvalue() if hasattr(img, "getvalue") else img.read()
        with st.spinner(t("Extracting text…", "テキスト抽出中…")):
            resp = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Extract all text from this image."}],
                files=[{"filename": "doc.jpg", "data": img_bytes}]
            )
        text = resp.choices[0].message.content
        st.subheader(t("📝 Extracted Text", "📝 抽出テキスト"))
        st.text_area("", text, height=300)

# --- DOCUMENT UPLOAD & SUMMARY ---
with st.expander(t("📁 Upload & Summarize Documents", "📁 ドキュメントアップロード & 要約")):
    uploaded = st.file_uploader(
        t("Select PDF/TXT files", "PDF/TXT ファイルを選択"),
        type=["pdf", "txt"],
        accept_multiple_files=True
    )
    for f in uploaded:
        name = f.name
        if name not in st.session_state.uploaded_filenames:
            content = ""
            try:
                if f.type == "application/pdf":
                    doc = fitz.open(stream=f.read(), filetype="pdf")
                    for page in doc:
                        content += page.get_text()
                else:
                    content = f.read().decode("utf-8")
                st.session_state.document_content[name] = content
                st.session_state.uploaded_filenames.append(name)
                # Summarize and generate questions
                summary_resp = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful AI assistant."},
                        {"role": "user", "content": f"Summarize and ask 5 questions based on the document:\n\n{content}"}
                    ]
                )
                st.session_state.document_summary[name] = summary_resp.choices[0].message.content
            except Exception as e:
                st.error(f"Error processing {name}: {e}")

# Display summaries
if st.session_state.document_summary:
    st.subheader(t("📄 Document Summaries & Questions", "📄 ドキュメント要約 & 質問"))
    for name, summ in st.session_state.document_summary.items():
        st.markdown(f"**🗂️ {name}**")
        st.markdown(summ)
        st.markdown("---")

# --- INTERACTIVE Q&A ---
st.subheader(t("Ask Your Question", "質問を入力"))
with st.form("qa_form", clear_on_submit=True):
    cols = st.columns([8, 2])
    user_q = cols[0].text_input(t("Enter question...", "質問を入力..."))
    ask_btn = cols[1].form_submit_button(t("Ask", "送信"))

if ask_btn and user_q:
    docs = "\n\n".join(st.session_state.document_content.values())
    if not docs:
        st.warning(t("Please upload documents first.", "先にドキュメントをアップロードしてください。"))
    else:
        st.session_state.chat_history.append({"role": "user", "content": user_q})
        try:
            qa_resp = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a document-savvy AI assistant."},
                    {"role": "user", "content": f"{docs}\n\nQuestion: {user_q}"}
                ]
            )
            answer = qa_resp.choices[0].message.content
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.markdown(answer)
        except OpenAIError as e:
            st.error(f"OpenAI API Error: {e}")

# --- CHAT HISTORY DISPLAY ---
if st.session_state.chat_history:
    st.subheader("💬 Chat History")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- FEEDBACK ---
st.write("**Was this helpful?**")
col_yes, col_no = st.columns([1,1])
if col_yes.button("👍 Yes"):
    st.success(t("Thanks for your feedback!", "フィードバックありがとうございます！"))
if col_no.button("👎 No"):
    st.info(t("Feedback noted.", "フィードバックを記録しました。"))

# --- FEEDBACK REVIEW ---
if st.session_state.feedback_entries:
    st.subheader("📬 Submitted Feedback")
    for idx, fb in enumerate(st.session_state.feedback_entries):
        role_icon = "👍" if fb.get("helpful") else "👎"
        st.markdown(f"- Entry {idx+1}: {role_icon} @ {fb.get('timestamp')}")
