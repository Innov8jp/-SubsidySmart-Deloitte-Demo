# --- main.py ---
from app.ocr_utils import extract_text_from_image
from app.gpt_utils import summarize_document, generate_exec_report
from app.ui_utils import t, init_session

import streamlit as st
import fitz  # PyMuPDF
from PIL import Image as PilImage
from io import BytesIO
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(
    page_title="DeloitteSmart™ - AI Assistant",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- API KEY ---
openai_api_key = st.secrets.get("OPENAI_API_KEY")
if not openai_api_key:
    st.sidebar.error("❌ OpenAI API key not found. Configure in Streamlit secrets.")
    st.stop()

# --- LANGUAGE & SESSION ---
lang = st.sidebar.radio("🌐 Language / 言語", ["English", "日本語"], index=0)
st.session_state.language = lang
init_session()

# --- TITLE ---
st.title(t("DeloitteSmart™: AI Assistant for Smarter Services", "DeloitteSmart™: M&Aとドキュメント解析のためのAIアシスタント"))

# --- OCR CAPTURE ---
with st.expander(t("📸 OCR - Camera or Upload", "📸 OCR カメラまたはアップロード")):
    img = st.camera_input(t("Capture Image", "写真を撮影")) or st.file_uploader(t("Or upload image", "または画像をアップロード"), type=["png", "jpg", "jpeg"])
    if img and st.button(t("Extract Text", "文字を抽出")):
        text = extract_text_from_image(img)
        if text:
            st.session_state.document_content["Captured Image"] = text
            st.text_area(t("Extracted Text", "抽出されたテキスト"), text, height=300)

# --- DOCUMENT UPLOAD ---
with st.expander(t("📁 Upload Documents", "📁 ドキュメントをアップロード"), expanded=True):
    files = st.file_uploader(t("Select PDF/TXT files", "PDF/TXTファイルを選択"), type=["pdf", "txt"], accept_multiple_files=True)
    for f in files:
        if f.name not in st.session_state.uploaded_filenames:
            try:
                content = fitz.open(stream=f.read(), filetype="pdf") if f.type == "application/pdf" else f.read().decode("utf-8")
                content_text = "".join([page.get_text() for page in content]) if f.type == "application/pdf" else content
                st.session_state.document_content[f.name] = content_text
                st.session_state.uploaded_filenames.append(f.name)
                summarize_document(f.name, content_text)
            except Exception as e:
                st.error(f"Error processing {f.name}: {e}")

# --- DOCUMENT SUMMARY ---
if st.session_state.document_summary:
    st.subheader(t("📄 Summaries", "📄 要約"))
    for doc, summary in st.session_state.document_summary.items():
        with st.expander(f"🗂️ {doc}"):
            st.markdown(summary)

# --- CHAT ---
st.subheader(t("💬 Ask Questions", "質問"))
prompt = st.chat_input(t("Type your question...", "質問を入力..."))
if prompt:
    docs = "\n\n".join(st.session_state.document_content.values())
    if not docs:
        st.warning(t("Please add or capture a document first.", "先に文書を追加または撮影してください"))
    else:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        from openai import OpenAIError
        import openai
        openai.api_key = openai_api_key
        try:
            ans = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a knowledgeable AI assistant."},
                    {"role": "user", "content": f"{docs}\n\nQuestion: {prompt}"}
                ]
            ).choices[0].message.content
            st.session_state.chat_history.append({"role": "assistant", "content": ans})
        except OpenAIError as e:
            st.error(f"OpenAI API Error: {e}")

for idx, msg in enumerate(st.session_state.chat_history):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            c1, c2 = st.columns([1, 1])
            if c1.button("👍", key=f"yes{idx}"):
                st.session_state.feedback_entries.append({"helpful": True, "timestamp": datetime.now().isoformat()})
            if c2.button("👎", key=f"no{idx}"):
                st.session_state.feedback_entries.append({"helpful": False, "timestamp": datetime.now().isoformat()})

# --- EXEC REPORT DOWNLOAD ---
st.markdown("---")
if st.button(t("Download Exec Report", "エグゼクティブレポートをダウンロード")):
    report_txt = generate_exec_report()
    if report_txt:
        st.download_button(
            t("Download Report", "レポートをダウンロード"),
            data=report_txt,
            file_name="Exec_Report.txt",
            mime="text/plain"
        )
