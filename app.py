# DeloitteSmart™ AI Assistant – Final UAT-Passed Version with Chat-Centric “Download Exec Report”

import streamlit as st
import openai
import fitz  # PyMuPDF for PDF parsing
from datetime import datetime
from openai import OpenAIError
from io import BytesIO
from PIL import Image
from fpdf import FPDF
import textwrap

# --- CONFIGURATION ---
st.set_page_config(
    page_title="DeloitteSmart™ - AI Assistant",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- OPENAI INIT ---
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

# --- SIDEBAR ANALYTICS ---
st.sidebar.image("deloitte_logo.png", width=200)
st.sidebar.markdown("**Powered by Innov8**")
st.sidebar.markdown("Version 1.0 | Secure & Scalable")
st.sidebar.markdown("---")
st.sidebar.subheader(t("Analytics", "分析"))
yes_count = sum(1 for f in st.session_state.get("feedback_entries", []) if f.get("helpful"))
no_count = sum(1 for f in st.session_state.get("feedback_entries", []) if not f.get("helpful"))
st.sidebar.metric(t("Helpful", "好評"), yes_count)
st.sidebar.metric(t("Not Helpful", "不評"), no_count)

# --- SESSION STATE DEFAULTS ---
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

# --- MAIN AREA ---
col_main, _ = st.columns([3,1])
with col_main:
    st.title(t(
        "DeloitteSmart™: AI Assistant for Smarter Services",
        "DeloitteSmart™: M&Aとドキュメント解析のためのAIアシスタント"
    ))

    # Camera OCR
    enable_cam = st.checkbox(t("📸 Enable Camera OCR", "📸 カメラOCRを有効にする"))
    if enable_cam:
        st.subheader(t("Document Capture & OCR", "ドキュメント撮影 & OCR"))
        tab1, tab2 = st.tabs([t("Live Capture","ライブ撮影"), t("Upload Image","画像をアップロード")])
        with tab1:
            img = st.camera_input(t("Capture via camera","カメラで撮影"))
        with tab2:
            img = st.file_uploader(t("Upload image file","画像ファイルをアップロード"), type=["png","jpg","jpeg"])
        if img:
            st.image(img, use_container_width=True)
            if st.button(t("Extract Text from Image","画像からテキストを抽出")):
                img_bytes = img.getvalue() if hasattr(img,"getvalue") else img.read()
                try:
                    import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from PIL import Image as PilImage

                    pil = PilImage.open(BytesIO(img_bytes))
                    text = pytesseract.image_to_string(pil)
                except ModuleNotFoundError:
                    st.error(t("pytesseract not installed. Run pip install pytesseract.",
                                    "pytesseractがインストールされていません。pip install pytesseractを実行してください。"))
                    text = ""
                except Exception as e:
                    st.error(t(f"OCR failed: {e}", f"OCRに失敗しました: {e}"))
                    text = ""
                st.session_state.document_content["Captured Image"] = text
                st.subheader(t("📝 Extracted Text","📝 抽出テキスト"))
                st.text_area("", text, height=300)

    # File upload & summary
    with st.expander(t("📁 Upload & Summarize Documents","📁 ドキュメントアップロード & 要約"), expanded=True):
        files = st.file_uploader(t("Select PDF/TXT files","PDF/TXTを選択"), type=["pdf","txt"], accept_multiple_files=True)
        for f in files:
            if f.name not in st.session_state.uploaded_filenames:
                content = ""
                try:
                    if f.type=="application/pdf":
                        doc=fitz.open(stream=f.read(),filetype="pdf")
                        content = "".join([page.get_text() for page in doc])
                    else:
                        content = f.read().decode("utf-8")
                    st.session_state.document_content[f.name]=content
                    st.session_state.uploaded_filenames.append(f.name)
                    resp=openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role":"system","content":"You are an expert AI consultant."},
                            {"role":"user","content":f"Summarize and ask 5 smart questions based on the document:\n{content}"}
                        ]
                    )
                    st.session_state.document_summary[f.name]=resp.choices[0].message.content
                except OpenAIError as e:
                    st.error(f"Error processing {f.name}: {e}")

    # Display summaries
    if st.session_state.document_summary:
        st.subheader(t("📄 Document Summaries & Questions","📄 ドキュメント要約 & 質問"))
        for doc, summ in st.session_state.document_summary.items():
            st.markdown(f"**🗂️ {doc}**")
            st.markdown(summ)
            st.markdown("---")

    # Chat & Q&A
    st.subheader(t("Chat & Ask Questions","チャット & 質問"))
    prompt=st.chat_input(t("Type your question...","質問を入力..."))
    if prompt:
        docs="\n\n".join(st.session_state.document_content.values())
        if not docs:
            st.warning(t("Please add or capture a document first.","先にドキュメントを追加または撮影してください。"))
        else:
            st.session_state.chat_history.append({"role":"user","content":prompt})
            try:
                ans=openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role":"system","content":"You are a knowledgeable AI assistant."},
                        {"role":"user","content":f"{docs}\n\nQuestion: {prompt}"}
                    ]
                ).choices[0].message.content
                st.session_state.chat_history.append({"role":"assistant","content":ans})
            except OpenAIError as e:
                st.error(f"OpenAI API Error: {e}")

    # Display chat history & feedback
    for idx,msg in enumerate(st.session_state.chat_history):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"]=="assistant":
                c1,c2=st.columns([1,1])
                if c1.button("👍",key=f"yes{idx}"):
                    st.session_state.feedback_entries.append({"helpful":True,"timestamp":datetime.now().isoformat()})
                if c2.button("👎",key=f"no{idx}"):
                    st.session_state.feedback_entries.append({"helpful":False,"timestamp":datetime.now().isoformat()})

                    # Download Exec Report button after chat
    st.markdown("---")
    if st.button(t("Download Exec Report", "エグゼクティブレポートをダウンロード")):
        # Combine all document content properly
        docs = st.session_state.document_content
        combined = "\n\n".join([f"Document: {name}\n{content}" for name, content in docs.items()])
        # Generate executive summary
        summary_resp = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a top-tier consultant AI."},
                {"role": "user", "content": f"Provide an executive summary:\n{combined}"}
            ]
        )
        exec_sum = summary_resp.choices[0].message.content
        # Generate smart questions
        questions_resp = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Generate 5 smart questions per document."},
                {"role": "user", "content": f"Documents:\n{combined}"}
            ]
        )
        questions = questions_resp.choices[0].message.content
        # Build plain text report
        report_txt = """# Exec Summary & Smart Questions

"""
        report_txt += "## Executive Summary\n" + exec_sum + "\n\n"
        report_txt += "## Smart Questions\n" + questions + "\n"
        # Download as .txt
        st.download_button(
            t("Download Exec Report", "エグゼクティブレポートをダウンロード"),
            data=report_txt,
            file_name="Exec_Report.txt",
            mime="text/plain"
        )
# --- END ---
