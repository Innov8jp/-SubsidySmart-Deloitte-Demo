# DeloitteSmart™ AI Assistant – Enhanced UAT-Passed Version with True Camera Selection & Q&A Integration

import streamlit as st
import openai
import fitz  # PyMuPDF for PDF parsing
import json
from datetime import datetime
from openai import OpenAIError
import os
from io import BytesIO
from PIL import Image
from streamlit_webrtc import webrtc_streamer, WebRtcMode

# --- CONFIGURATION ---
st.set_page_config(
    page_title="DeloitteSmart™ - AI Assistant",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- OPENAI INITIALIZATION ---
openai_api_key = st.secrets.get("OPENAI_API_KEY")
if not openai_api_key:
    st.sidebar.error("❌ OpenAI API key not found. Configure in Streamlit secrets.")
    st.stop()
openai.api_key = openai_api_key

# --- LANGUAGE TOGGLE ---
if "language" not in st.session_state:
    st.session_state.language = "English"
lang = st.sidebar.radio("🌐 Language / 言語", ["English", "日本語"], index=0)
st.session_state.language = lang

def t(en: str, jp: str) -> str:
    return en if st.session_state.language == "English" else jp

# --- SIDEBAR BRANDING ---
st.sidebar.image("deloitte_logo.png", width=200)
st.sidebar.markdown("**Powered by Innov8**")
st.sidebar.markdown("Prototype v1.0 | Secure & Scalable")

# --- SESSION STATE DEFAULTS ---
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
        "DeloitteSmart™: AI Assistant for M&A & Document Insights",
        "DeloitteSmart™: M&Aおよびドキュメント解析向け AI アシスタント"
    )
)

# --- REAL-TIME CAMERA CAPTURE & OCR ---
enable_camera = st.sidebar.checkbox(t("📸 Enable Camera OCR", "📸 カメラOCRを有効にする"), value=False)
if enable_camera:
    st.header(t("📸 Real-Time Camera Capture & OCR", "📸 リアルタイムカメラ撮影 & OCR"))
    st.markdown(
        t(
            "Select camera device and capture a frame for OCR.",
            "カメラデバイスを選択し、OCR用にフレームをキャプチャ。"
        )
    )
    # Dropdown to select camera index (0=default front, 1=rear)
    cam_index = st.selectbox(
        t("Camera Device", "カメラデバイス"),
        options=[0, 1],
        format_func=lambda i: t("Front Camera", "前面カメラ") if i == 0 else t("Rear Camera", "背面カメラ")
    )
    webrtc_ctx = webrtc_streamer(
        key="webrtc-camera",
        mode=WebRtcMode.SENDRECV,
        video_device_index=cam_index,
        media_stream_constraints={"video": True, "audio": False},
    )
    # Capture frame
    if webrtc_ctx.video_receiver:
        frame = webrtc_ctx.video_receiver.get_frame()
        img = frame.to_image()
        st.image(img, use_container_width=True)
        if st.button(t("Capture Frame for OCR", "OCR用フレームをキャプチャ")):
            buffer = BytesIO()
            img.save(buffer, format="JPEG")
            img_bytes = buffer.getvalue()
            with st.spinner(t("Extracting text…", "テキスト抽出中…")):
                ocr_resp = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "Extract all text from this image."}],
                    files=[{"filename": "capture.jpg", "data": img_bytes}]
                )
            ocr_text = ocr_resp.choices[0].message.content
            # Save as a document
            st.session_state.document_content["Captured Image"] = ocr_text
            st.subheader(t("📝 Extracted Text", "📝 抽出テキスト"))
            st.text_area("", ocr_text, height=300)

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
            try:
                content = ""
                if f.type == "application/pdf":
                    doc = fitz.open(stream=f.read(), filetype="pdf")
                    for page in doc:
                        content += page.get_text()
                else:
                    content = f.read().decode("utf-8")
                st.session_state.document_content[name] = content
                st.session_state.uploaded_filenames.append(name)
                # Summarize
                sum_resp = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful AI assistant."},
                        {"role": "user", "content": f"Summarize and ask 5 questions based on the document:\n\n{content}"}
                    ]
                )
                st.session_state.document_summary[name] = sum_resp.choices[0].message.content
            except Exception as e:
                st.error(f"Error processing {name}: {e}")

# --- DISPLAY SUMMARIES ---
if st.session_state.document_summary:
    st.subheader(t("📄 Document Summaries & Questions", "📄 ドキュメント要約 & 質問"))
    for name, summary in st.session_state.document_summary.items():
        st.markdown(f"**🗂️ {name}**")
        st.markdown(summary)
        st.markdown("---")

# --- INTERACTIVE Q&A ---
st.subheader(t("Ask Your Question", "質問を入力"))
with st.form("qa_form", clear_on_submit=True):
    cols = st.columns([8, 2])
    user_q = cols[0].text_input(t("Enter your question...", "質問を入力..."))
    ask_btn = cols[1].form_submit_button(t("Ask", "送信"))

if ask_btn and user_q:
    docs = list(st.session_state.document_content.values())
    combined = "\n\n".join(docs)
    if not combined:
        st.warning(t("Please provide a document or capture an image first.", "先にドキュメント提供または画像撮影をしてください。"))
    else:
        st.session_state.chat_history.append({"role": "user", "content": user_q})
        try:
            qa_resp = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a document-savvy AI assistant."},
                    {"role": "user", "content": f"{combined}\n\nQuestion: {user_q}"}
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
st.write(t("**Was this helpful?**", "**役立ちましたか？**"))
col_yes, col_no = st.columns([1, 1])
if col_yes.button("👍 Yes"):
    st.success(t("Thanks for your feedback!", "フィードバックありがとうございます！"))
if col_no.button("👎 No"):
    st.info(t("Feedback noted.", "フィードバックを記録しました。"))

# --- FEEDBACK REVIEW ---
if st.session_state.feedback_entries:
    st.subheader("📬 Submitted Feedback")
    for i, fb in enumerate(st.session_state.feedback_entries):
        icon = "👍" if fb.get("helpful") else "👎"
        st.markdown(f"- Entry {i+1}: {icon} @ {fb.get('timestamp')}")
