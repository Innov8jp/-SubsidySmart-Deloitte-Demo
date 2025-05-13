# DeloitteSmart™ AI Assistant – Full Version (Enhanced Multi-Doc Summarizer, Persistent Chat, Downloadable Report, Feedback)

import streamlit as st
import openai
import fitz  # PyMuPDF
import json
from datetime import datetime
from openai import OpenAIError
import os

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

# --- CONTINUED QUESTION INPUT ---
if st.session_state.document_content:
    st.subheader("💬 Chat with DeloitteSmart™ AI")
    with st.form(key="chat_form"):
        question_input = st.text_input("Ask your question:", placeholder="e.g., What subsidy best suits an AI startup?")
        submit_button = st.form_submit_button(label="Send")

    if submit_button and question_input.strip():
        question = question_input.strip()
        openai.api_key = openai_api_key
        combined_docs = "

".join(st.session_state.document_content.values())
