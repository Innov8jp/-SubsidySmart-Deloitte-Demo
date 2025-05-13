# DeloitteSmart™ AI Assistant – Full Version (Enhanced Multi-Doc Summarizer, Persistent Chat, Downloadable Report, Feedback)

import streamlit as st
import openai
import fitz  # PyMuPDF
import json
from datetime import datetime
from openai import OpenAIError
import os
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
from PIL import Image

# --- CONFIG ---
st.set_page_config(
    page_title="DeloitteSmart™ - AI Assistant",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LANGUAGE TOGGLE ---
language = st.sidebar.radio("🌐 Language / 言語", ["English", "日本語"], index=0)

# --- SIDEBAR ---
rear_camera_enabled = st.sidebar.checkbox("📷 Enable Rear Camera Mode")
st.session_state.enable_camera = st.sidebar.checkbox("📸 Enable Camera Input")
with st.sidebar:
    st.image("deloitte_logo.png", width=200)
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    st.markdown("✅ OpenAI API key is pre-configured.")
    st.markdown("Powered by [Innov8]")
    st.markdown("Prototype Version 1.0")
    st.markdown("Secure | Scalable | Smart")

# --- SESSION STATE SETUP ---
session_defaults = {
    "chat_history": [],
    "user_question": "",
    "feedback": [],
    "show_feedback": False,
    "enable_camera": False,
    "document_content": {},
    "document_summary": {},
    "uploaded_filenames": []
}
for key, default in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- MAIN PAGE ---
title_text = "DeloitteSmart™: Your AI Assistant for Faster, Smarter Decisions" if language == "English" else "DeloitteSmart™：より速く、よりスマートな意思決定を支援するAIアシスタント"
st.title(title_text)

# --- FILE UPLOAD ---
with st.expander("📁 Upload Documents (PDF, TXT)"):
    uploaded_files = st.file_uploader("", type=["pdf", "txt"], accept_multiple_files=True)
    if uploaded_files:
        for file in uploaded_files:
            filename = file.name
            file_bytes = file.read()
            if filename not in st.session_state.uploaded_filenames:
                doc_text = ""
                if file.type == "application/pdf":
                    try:
                        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                            for page in doc:
                                doc_text += page.get_text()
                    except Exception as e:
                        st.error(f"PDF extraction error: {str(e)}")
                        continue
                elif file.type == "text/plain":
                    doc_text += file_bytes.decode("utf-8")

                st.session_state.document_content[filename] = doc_text
                st.session_state.uploaded_filenames.append(filename)

                # Summarize
                openai.api_key = openai_api_key
                prompt = f"""
You are a highly trained consultant. Summarize the following content and generate 5 smart questions to ask the client.

Document:
{doc_text}
"""
                try:
                    response = openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are an AI assistant specialized in summarizing and extracting smart questions."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    summary_result = response.choices[0].message.content
                    st.session_state.document_summary[filename] = summary_result
                except Exception as e:
                    st.error(f"Summary generation error for {filename}: {str(e)}")

# --- SHOW SUMMARIES ---
if st.session_state.document_summary:
    st.subheader("📄 Summaries & Smart Questions")
    for fname, summary in st.session_state.document_summary.items():
        st.markdown(f"#### 🗂️ {fname}")
        st.markdown(summary)
        st.markdown("---")

# --- CAMERA INPUT (if enabled) ---
if st.session_state.enable_camera:
    st.subheader("📸 Capture Image for Document Input")
    if not OCR_AVAILABLE:
        st.warning("OCR is not available. Please install pytesseract and the Tesseract engine.")
    else:
        camera_label = "Take a picture using rear camera" if rear_camera_enabled else "Take a picture"
        captured_image = st.camera_input(camera_label)
        if captured_image:
            try:
                image = Image.open(captured_image)
                extracted_text = pytesseract.image_to_string(image)
                cam_doc_name = f"camera_capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                st.session_state.document_content[cam_doc_name] = extracted_text
                st.session_state.uploaded_filenames.append(cam_doc_name)

                # Generate summary from captured image
                openai.api_key = openai_api_key
                prompt = f"""
You are a highly trained consultant. Summarize the following content and generate 5 smart questions to ask the client.

Document:
{extracted_text}
"""
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an AI assistant specialized in summarizing and extracting smart questions."},
                        {"role": "user", "content": prompt}
                    ]
                )
                cam_summary = response.choices[0].message.content
                st.session_state.document_summary[cam_doc_name] = cam_summary
                st.success("✅ Image captured and processed with AI summary and smart questions.")
            except Exception as e:
                st.error(f"❌ Failed to process camera input: {str(e)}")

# --- CONTINUED QUESTION INPUT ---
combined_docs = "\n\n".join(st.session_state.document_content.values())
