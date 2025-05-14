# DeloitteSmart™ AI Assistant – Final UAT-Passed Version with True Camera Selection & Q&A Integration

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
st.sidebar.markdown("Version 1.0 | Secure & Scalable")

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
        "DeloitteSmart™: AI Assistant for M&A & Insights",
        "DeloitteSmart™: M&Aと洞察のためのAIアシスタント"
    )
)

# --- CAMERA OCR SECTION ---
enable_cam = st.sidebar.checkbox(t("📸 Enable Camera OCR", "📸 カメラOCRを有効にする"), value=False)
if enable_cam:
    st.header(t("📸 Camera OCR Capture", "📸 カメラOCR取得"))
    cam_idx = st.selectbox(
        t("Camera Device", "カメラデバイス"),
        options=[0, 1],
        format_func=lambda i: t("Front Camera", "前面カメラ") if i == 0 else t("Rear Camera", "背面カメラ"),
        key="camera_device"
    )
    # Use streamlit-webrtc with selected device
    try:
        webrtc_ctx = webrtc_streamer(
            key="camera",
            mode=WebRtcMode.SENDRECV,
            video_device_index=cam_idx,
            async_processing=False
        )
    except Exception:
        st.warning(t(
            "Selected camera not available. Please capture/upload an image instead.",
            "選択したカメラが利用できません。代わりに画像を撮影またはアップロードしてください。"
        ))
        webrtc_ctx = None

    # If camera initialized and receiving frames
    if webrtc_ctx and webrtc_ctx.video_receiver:
        frame = webrtc_ctx.video_receiver.get_frame()
        img = frame.to_image()
        st.image(img, use_container_width=True)
        if st.button(t("Capture for OCR", "OCR用に取得")):
            buf = BytesIO()
            img.save(buf, format="JPEG")
            data = buf.getvalue()
            with st.spinner(t("Extracting text…", "テキスト抽出中…")):
                try:
                    resp = openai.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role":"user","content":"Extract text from this image."}],
                        files=[{"filename":"capture.jpg","data":data}]
                    )
                    text = resp.choices[0].message.content
                except Exception:
                    st.error(t("OCR extraction failed.", "OCR抽出に失敗しました。"))
                    text = ""
            st.session_state.document_content["Captured Image"] = text
            st.subheader(t("📝 OCR Text", "📝 OCRテキスト"))
            st.text_area("", text, height=300)

# --- FILE UPLOAD / SUMMARY ---
with st.expander(t("📁 Upload & Summarize", "📁 アップロードと要約")):
    uploads = st.file_uploader(
        t("Select PDF/TXT files", "PDF/TXTを選択"),
        type=["pdf","txt"], accept_multiple_files=True
    )
    for f in uploads:
        name = f.name
        if name not in st.session_state.uploaded_filenames:
            try:
                content = ""
                if f.type == "application/pdf":
                    doc = fitz.open(stream=f.read(), filetype="pdf")
                    for p in doc: content += p.get_text()
                else:
                    content = f.read().decode()
                st.session_state.document_content[name] = content
                st.session_state.uploaded_filenames.append(name)
                sumr = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role":"system","content":"You are an expert AI consultant."},
                        {"role":"user","content":f"Summarize and ask 5 smart questions:\n{content}"}
                    ]
                )
                st.session_state.document_summary[name] = sumr.choices[0].message.content
            except Exception as e:
                st.error(f"Error processing {name}: {e}")

# --- DISPLAY SUMMARIES ---
if st.session_state.document_summary:
    st.subheader(t("📄 Summaries & Questions", "📄 要約と質問"))
    for doc, summ in st.session_state.document_summary.items():
        st.markdown(f"**🗂️ {doc}**")
        st.markdown(summ)
        st.markdown("---")

# --- INTERACTIVE Q&A ---
st.subheader(t("Ask Questions", "質問する"))
with st.form("qa_form", clear_on_submit=True):
    cols = st.columns([8,2])
    query = cols[0].text_input(t("Enter question...","質問を入力..."))
    send = cols[1].form_submit_button(t("Ask","送信"))

if send and query:
    docs = "\n\n".join(st.session_state.document_content.values())
    if not docs:
        st.warning(t("Please add or capture a document first.","先にドキュメントを追加または撮影してください。"))
    else:
        st.session_state.chat_history.append({"role":"user","content":query})
        try:
            resp = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role":"system","content":"You are a knowledgeable AI assistant."},
                    {"role":"user","content":f"{docs}\n\nQuestion: {query}"}
                ]
            )
            ans = resp.choices[0].message.content
            st.session_state.chat_history.append({"role":"assistant","content":ans})
            st.markdown(ans)
        except OpenAIError as e:
            st.error(f"OpenAI API Error: {e}")

# --- CHAT HISTORY ---
if st.session_state.chat_history:
    st.subheader("💬 Chat History")
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

# --- REPORT GENERATION ---
st.subheader(t("Generate Report & Dashboard","レポートとダッシュボード生成"))
if st.button(t("Build Report","レポート作成")):
    docs = st.session_state.document_content
    combined = "\n\n".join([f"Document: {d}\n{c}" for d,c in docs.items()])
    sumr = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":"You are a top-tier consultant AI."},
            {"role":"user","content":f"Provide an executive summary:\n{combined}"}
        ]
    )
    exec_sum = sumr.choices[0].message.content
    qst = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":"Generate 5 smart questions per document."},
            {"role":"user","content":f"Documents:\n{combined}"}
        ]
    )
    questions = qst.choices[0].message.content
    report = f"# Consolidated Report\n\n## Executive Summary\n{exec_sum}\n\n## Smart Questions\n{questions}\n"
    st.download_button(
        t("Download Report","レポートをダウンロード"),
        data=report,
        file_name="DeloitteSmart_Report.md",
        mime="text/markdown"
    )
    yes = sum(1 for f in st.session_state.feedback_entries if f.get("helpful"))
    no = sum(1 for f in st.session_state.feedback_entries if not f.get("helpful"))
    st.subheader(t("Feedback Analytics","フィードバック分析"))
    st.metric(t("Helpful","好評"), yes)
    st.metric(t("Not Helpful","不評"), no)

# --- FEEDBACK ---
st.write(t("**Was this helpful?**","**役立ちましたか？**"))
col1, col2 = st.columns([1,1])
if col1.button("👍 Yes"): st.session_state.feedback_entries.append({"helpful":True,"timestamp":datetime.now().isoformat()})
if col2.button("👎 No"): st.session_state.feedback_entries.append({"helpful":False,"timestamp":datetime.now().isoformat()})

# --- END ---
