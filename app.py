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
col_main, _ = st.columns([3, 1])
with col_main:
    st.title(t(
        "DeloitteSmart™: AI Assistant for Smarter Services",
        "DeloitteSmart™: M&Aとドキュメント解析のためのAIアシスタント"
    ))

    # Camera OCR
    enable_cam = st.checkbox(t("📸 Enable Camera OCR", "📸 カメラOCRを有効にする"))
    if enable_cam:
        st.subheader(t("Document Capture & OCR", "ドキュメント撮影 & OCR"))
        tab1, tab2 = st.tabs([t("Live Capture", "ライブ撮影"), t("Upload Image", "画像をアップロード")])
        with tab1:
            img = st.camera_input(t("Capture via camera", "カメラで撮影"))
        with tab2:
            img = st.file_uploader(t("Upload image file", "画像ファイルをアップロード"), type=["png", "jpg", "jpeg"])
        if img:
            st.image(img, use_container_width=True)
            if st.button(t("Extract Text from Image", "画像からテキストを抽出")):
                img_bytes = img.getvalue() if hasattr(img, "getvalue") else img.read()
                try:
                    import pytesseract
                    pytesseract.pytesseract.tesseract_cmd = r"C:\\Users\\asifb\\OneDrive\\documents\\tesseract.exe"
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
                st.subheader(t("📝 Extracted Text", "📝 抽出テキスト"))
                st.text_area("", text, height=300)
