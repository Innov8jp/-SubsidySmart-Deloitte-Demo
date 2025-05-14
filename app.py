# DeloitteSmart™ AI Assistant – Fresh UAT-Passed Version

import streamlit as st
import openai
import fitz  # PyMuPDF for PDF parsing
from datetime import datetime
from openai import OpenAIError
from io import BytesIO
from PIL import Image

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
lang = st.sidebar.radio(
    "🌐 Language / 言語",
    ["English", "日本語"],
    index=0
)
st.session_state.language = lang

def t(en: str, jp: str) -> str:
    return en if st.session_state.language == "English" else jp

# --- SIDEBAR BRANDING ---
st.sidebar.image("deloitte_logo.png", width=200)
st.sidebar.markdown("**Powered by Innov8**")
st.sidebar.markdown("Version 1.0 | Secure & Scalable")

# --- SESSION STATE DEFAULTS ---
def init_session():
    for key, val in {
        "chat_history": [],
        "document_content": {},
        "document_summary": {},
        "uploaded_filenames": [],
        "feedback_entries": []
    }.items():
        if key not in st.session_state:
            st.session_state[key] = val
init_session()

# --- MAIN TITLE ---
st.title(
    t(
        "DeloitteSmart™: AI Assistant for M&A & Document Insights",
        "DeloitteSmart™: M&A とドキュメント解析のための AI アシスタント"
    )
)

# --- CAMERA OCR SECTION ---
enable_cam = st.sidebar.checkbox(
    t("📸 Enable Camera OCR", "📸 カメラOCRを有効にする"),
    value=False
)
if enable_cam:
    st.header(t("📸 Document Capture & OCR", "📸 ドキュメント撮影 & OCR"))
    st.markdown(
        t(
            "Use Front Camera for live capture or upload from Rear Camera tab.",
            "前面カメラでライブ撮影、または背面カメラ写真をアップロード。"
        )
    )
    tab_front, tab_rear = st.tabs([
        t("Front Camera", "前面カメラ"),
        t("Rear Camera", "背面カメラ")
    ])
    with tab_front:
        img = st.camera_input(t("Capture with front camera", "前面カメラで撮影"))
    with tab_rear:
        img = st.file_uploader(
            t("Upload image taken by rear camera", "背面カメラで撮影した画像をアップロード"),
            type=["png","jpg","jpeg"]
        )
    if img:
        st.image(img, use_container_width=True)
        img_bytes = img.getvalue() if hasattr(img, "getvalue") else img.read()
        with st.spinner(t("Extracting text…", "テキスト抽出中…")):
            try:
                resp = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role":"user","content":"Extract all text from this image."}
                    ],
                    files=[{"filename":"capture.jpg","data":img_bytes}]
                )
                text = resp.choices[0].message.content
            except Exception:
                st.error(t("OCR extraction failed.", "OCR抽出に失敗しました。"))
                text = ""
        st.session_state.document_content["Captured Image"] = text
        st.subheader(t("📝 Extracted Text", "📝 抽出テキスト"))
        st.text_area("", text, height=300)

# --- FILE UPLOAD & SUMMARY ---
with st.expander(t("📁 Upload & Summarize Documents", "📁 ドキュメントアップロード & 要約")):
    uploads = st.file_uploader(
        t("Select PDF/TXT files", "PDF/TXT ファイルを選択"),
        type=["pdf","txt"],
        accept_multiple_files=True
    )
    for f in uploads:
        name = f.name
        if name not in st.session_state.uploaded_filenames:
            try:
                content = ""
                if f.type == "application/pdf":
                    doc = fitz.open(stream=f.read(), filetype="pdf")
                    for p in doc:
                        content += p.get_text()
                else:
                    content = f.read().decode("utf-8")
                st.session_state.document_content[name] = content
                st.session_state.uploaded_filenames.append(name)
                sumr = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role":"system","content":"You are an expert AI consultant."},
                        {"role":"user","content":f"Summarize and ask 5 smart questions based on the document:\n{content}"}
                    ]
                )
                st.session_state.document_summary[name] = sumr.choices[0].message.content
            except Exception as e:
                st.error(f"Error processing {name}: {e}")

# --- DISPLAY SUMMARIES ---
if st.session_state.document_summary:
    st.subheader(t("📄 Document Summaries & Questions", "📄 ドキュメント要約 & 質問"))
    for doc, summ in st.session_state.document_summary.items():
        st.markdown(f"**🗂️ {doc}**")
        st.markdown(summ)
        st.markdown("---")

# --- INTERACTIVE Q&A ---
st.subheader(t("Ask Your Question", "質問する"))
with st.form("qa_form", clear_on_submit=True):
    cols = st.columns([8,2])
    query = cols[0].text_input(t("Enter question...", "質問を入力..."))
    send = cols[1].form_submit_button(t("Ask", "送信"))

if send and query:
    docs = "\n\n".join(st.session_state.document_content.values())
    if not docs:
        st.warning(t("Please add or capture a document first.", "先にドキュメントを追加または撮影してください。"))
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
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

# --- REPORT GENERATION & DASHBOARD ---
st.subheader(t("Generate Consolidated Report & Dashboard", "統合レポートとダッシュボード生成"))
if st.button(t("Build Report", "レポート作成")):
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
        t("Download Report", "レポートをダウンロード"),
        data=report,
        file_name="DeloitteSmart_Report.md",
        mime="text/markdown"
    )
    # Feedback analytics
    yes = sum(1 for f in st.session_state.feedback_entries if f.get("helpful"))
    no = sum(1 for f in st.session_state.feedback_entries if not f.get("helpful"))
    st.subheader(t("Feedback Analytics", "フィードバック分析"))
    st.metric(t("Helpful", "好評"), yes)
    st.metric(t("Not Helpful", "不評"), no)

# --- FEEDBACK ---
st.write(t("**Was this helpful?**", "**役立ちましたか？**"))
col1, col2 = st.columns([1,1])
if col1.button("👍 Yes"):
    st.session_state.feedback_entries.append({"helpful":True, "timestamp":datetime.now().isoformat()})
if col2.button("👎 No"):
    st.session_state.feedback_entries.append({"helpful":False, "timestamp":datetime.now().isoformat()})

# --- END ---
