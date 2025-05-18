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
            cam_img = st.camera_input(t("Capture via camera", "カメラで撮影"))
            if cam_img and st.button(t("Extract Text from Camera", "カメラからテキストを抽出"), key="extract_cam"):
                try:
                    import pytesseract
                    from PIL import Image as PilImage
                    cam_bytes = cam_img.getvalue()
                    cam_pil = PilImage.open(BytesIO(cam_bytes))
                    cam_text = pytesseract.image_to_string(cam_pil)
                    st.session_state.document_content["Camera Image"] = cam_text
                    st.subheader(t("📝 Extracted Text from Camera", "📝 カメラ画像からの抽出テキスト"))
                    st.text_area("", cam_text, height=200)
                except Exception as e:
                    st.error(t(f"OCR failed: {e}", f"OCRに失敗しました: {e}"))

        with tab2:
            file_img = st.file_uploader(t("Upload image file", "画像ファイルをアップロード"), type=["png", "jpg", "jpeg"])
            if file_img and st.button(t("Extract Text from Uploaded Image", "アップロード画像からテキストを抽出"), key="extract_upload"):
                try:
                    import pytesseract
                    from PIL import Image as PilImage
                    file_bytes = file_img.getvalue()
                    file_pil = PilImage.open(BytesIO(file_bytes))
                    file_text = pytesseract.image_to_string(file_pil)
                    st.session_state.document_content["Uploaded Image"] = file_text
                    st.subheader(t("📝 Extracted Text from Uploaded Image", "📝 アップロード画像からの抽出テキスト"))
                    st.text_area("", file_text, height=200)
                except Exception as e:
                    st.error(t(f"OCR failed: {e}", f"OCRに失敗しました: {e}"))

# The rest of the script remains unchanged.
# Ensure any downstream usage of st.session_state.document_content includes both "Camera Image" and "Uploaded Image" keys as needed.
