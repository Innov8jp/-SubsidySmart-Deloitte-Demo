# DeloitteSmart™ AI Assistant – Final UAT-Passed Version with Sidebar Analytics & PDF Reporting

import streamlit as st
import openai
import fitz  # PyMuPDF for PDF parsing
from datetime import datetime
from openai import OpenAIError
from io import BytesIO
from PIL import Image
from fpdf import FPDF  # for PDF report generation

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

# --- SIDEBAR BRANDING & TOOLS ---
st.sidebar.image("deloitte_logo.png", width=200)
st.sidebar.markdown("**Powered by Innov8**")
st.sidebar.markdown("Version 1.0 | Secure & Scalable")

# --- SESSION DEFAULTS ---
def init_session():
    defaults = {
        "chat_history": [],
        "document_content": {},
        "document_summary": {},
        "uploaded_filenames": [],
        "feedback_entries": []
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
init_session()

# --- MAIN LAYOUT ---
col_main, col_sidebar = st.columns([3, 1])
with col_main:
    st.title(
        t(
            "DeloitteSmart™: AI Assistant for M&A & Document Insights",
            "DeloitteSmart™: M&Aとドキュメント解析のためのAIアシスタント"
        )
    )

    # --- CAMERA OCR ---
    enable_cam = st.checkbox(t("📸 Enable Camera OCR", "📸 カメラOCRを有効にする"), key="cam_toggle")
    if enable_cam:
        st.subheader(t("Document Capture & OCR", "ドキュメント撮影 & OCR"))
        tab_live, tab_upload = st.tabs([
            t("Live Capture", "ライブ撮影"),
            t("Upload Image", "画像をアップロード")
        ])
        with tab_live:
            img = st.camera_input(t("Capture via camera", "カメラで撮影"))
        with tab_upload:
            img = st.file_uploader(
                t("Upload image file", "画像ファイルをアップロード"),
                type=["png","jpg","jpeg"]
            )

        if img:
            st.image(img, use_container_width=True)
            # Add explicit button to trigger OCR
            if st.button(t("Extract Text from Image", "画像からテキストを抽出")):
                img_bytes = img.getvalue() if hasattr(img, "getvalue") else img.read()
                with st.spinner(t("Extracting text…", "テキスト抽出中…")):
                    try:
                        resp = openai.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role":"user","content":"Extract all text from this image."}],
                            files=[{"filename":"capture.jpg","data":img_bytes}]
                        )
                        text = resp.choices[0].message.content
                    except Exception:
                        st.error(t("OCR extraction failed.", "OCR抽出に失敗しました。"))
                        text = ""
                # Store and display
                st.session_state.document_content["Captured Image"] = text
                st.subheader(t("📝 Extracted Text", "📝 抽出テキスト"))
                st.text_area("", text, height=300)
# --- FILE UPLOAD & SUMMARY ---
    with st.expander(t("📁 Upload & Summarize Documents", "📁 ドキュメントアップロード & 要約")):
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
    st.subheader(t("Ask Your Question", "質問を入力"))
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

# --- SIDEBAR CONTENT: REPORT & ANALYTICS ---
with col_sidebar:
    st.header(t("📊 Analytics & Report", "📊 分析 & レポート"))
    # Feedback analytics
    yes = sum(1 for f in st.session_state.feedback_entries if f.get("helpful"))
    no = sum(1 for f in st.session_state.feedback_entries if not f.get("helpful"))
    st.metric(t("Helpful", "好評"), yes)
    st.metric(t("Not Helpful", "不評"), no)
    st.markdown("---")
    # Generate PDF report
    if st.button(t("Generate PDF Report", "PDF レポートを生成")):
        docs = st.session_state.document_content
        combined = "\n\n".join([f"Document: {d}\n{c}" for d,c in docs.items()])
        # Executive summary
        sumr = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"You are a top-tier consultant AI."},
                {"role":"user","content":f"Provide an executive summary:\n{combined}"}
            ]
        )
        exec_sum = sumr.choices[0].message.content
        # Smart questions
        qst = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"Generate 5 smart questions per document."},
                {"role":"user","content":f"Documents:\n{combined}"}
            ]
        )
        questions = qst.choices[0].message.content
        # Build PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Consolidated Report", ln=1)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Executive Summary", ln=1)
        pdf.set_font("Arial", "", 11)
        for line in exec_sum.split("\n"):
            pdf.multi_cell(0, 6, line)
        pdf.ln(4)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Smart Questions", ln=1)
        pdf.set_font("Arial", "", 11)
        for line in questions.split("\n"):
            pdf.multi_cell(0, 6, line)
        # Export
        buf = BytesIO()
        pdf.output(buf)
        buf.seek(0)
        st.download_button(
            t("Download PDF Report", "PDF レポートをダウンロード"),
            data=buf,
            file_name="DeloitteSmart_Report.pdf",
            mime="application/pdf"
        )
