# DeloitteSmart™ AI Assistant – Full Version (PDF Summary, Multi-Question, Downloadable Report, Feedback)

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
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "user_question" not in st.session_state:
    st.session_state.user_question = ""
if "feedback" not in st.session_state:
    st.session_state.feedback = []
if "show_feedback" not in st.session_state:
    st.session_state.show_feedback = False
if "enable_camera" not in st.session_state:
    st.session_state.enable_camera = False
if "document_content" not in st.session_state:
    st.session_state.document_content = ""
if "document_summary" not in st.session_state:
    st.session_state.document_summary = ""

# --- MAIN PAGE ---
title_text = "DeloitteSmart™: Your AI Assistant for Faster, Smarter Decisions" if language == "English" else "DeloitteSmart™：より速く、よりスマートな意思決定を支援するAIアシスタント"
st.title(title_text)

# --- FILE UPLOAD ---
with st.expander("📁 Upload Documents (PDF, TXT)"):
    uploaded_files = st.file_uploader("", type=["pdf", "txt"], accept_multiple_files=True)
    if uploaded_files:
        doc_text = ""
        doc_names = []
        for file in uploaded_files:
            doc_names.append(file.name)
            file_bytes = file.read()
            if file.type == "application/pdf":
                try:
                    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                        for page in doc:
                            doc_text += page.get_text()
                except Exception as e:
                    st.error(f"PDF extraction error: {str(e)}")
            elif file.type == "text/plain":
                doc_text += file_bytes.decode("utf-8")

        st.session_state.document_content = doc_text

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
            st.session_state.document_summary = summary_result
            st.subheader("📄 Summary & Questions")
            st.markdown(summary_result)
        except Exception as e:
            st.error(f"Summary generation error: {str(e)}")

# --- CONTINUED QUESTION INPUT ---
if st.session_state.document_content:
    st.subheader("🔍 Ask More Questions About the Document")
    st.text_input("Your follow-up question:", key="user_question")
    if st.button("Ask AI"):
        question = st.session_state.user_question.strip()
        if question:
            openai.api_key = openai_api_key
            prompt = f"""
Refer to the following uploaded document and answer the question below:

Document Content:
{st.session_state.document_content}

User Question:
{question}
"""
            try:
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a Deloitte AI assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
                reply = response.choices[0].message.content
                st.markdown("**AI Answer:**")
                st.markdown(reply)

                entry = {
                    "question": question,
                    "answer": reply,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.chat_history.append(entry)
                st.session_state.show_feedback = True

            except Exception as e:
                st.error(f"AI response error: {str(e)}")

# --- DOWNLOAD REPORT ---
if st.session_state.document_summary:
    report_text = f"Summary and Smart Questions Generated on {datetime.now().strftime('%Y-%m-%d')}\n\n{st.session_state.document_summary}"
    st.download_button("📥 Download Report", report_text, file_name="deloitte_ai_summary.txt")

# --- FEEDBACK ---
if st.session_state.get("show_feedback") and st.session_state.chat_history:
    st.write("**Was this helpful?**")
    col_yes, col_no = st.columns([1, 1])
    with col_yes:
        if st.button("👍 Yes"):
            feedback_entry = {"helpful": True, "timestamp": datetime.now().isoformat()}
            st.session_state.feedback.append(feedback_entry)
            with open("feedback_log.json", "a", encoding="utf-8") as f:
                f.write(json.dumps(feedback_entry) + "\n")
            st.session_state.show_feedback = False
            st.success("Thank you for your feedback!")
    with col_no:
        if st.button("👎 No"):
            feedback_entry = {"helpful": False, "timestamp": datetime.now().isoformat()}
            st.session_state.feedback.append(feedback_entry)
            with open("feedback_log.json", "a", encoding="utf-8") as f:
                f.write(json.dumps(feedback_entry) + "\n")
            st.session_state.show_feedback = False
            st.info("Feedback noted. We'll use it to improve.")
