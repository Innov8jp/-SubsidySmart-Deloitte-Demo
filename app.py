# DeloitteSmart™ AI Assistant – Full Version (Enhanced Multi-Doc Summarizer, Camera OCR, Persistent Chat, Feedback, Downloadable Report)

import streamlit as st
import openai
import fitz  # PyMuPDF
import json
from datetime import datetime
from openai import OpenAIError
import os

# --- Optional OCR (Camera Text Extraction) ---

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
st.sidebar.image("deloitte_logo.png", width=200)
openai_api_key = st.secrets.get("OPENAI_API_KEY")
if openai_api_key:
    st.sidebar.success("✅ OpenAI API key is pre-configured.")
else:
    st.sidebar.error("❌ OpenAI API key not found.")
st.sidebar.markdown("Powered by [Innov8]")
st.sidebar.markdown("Prototype Version 1.0")
st.sidebar.markdown("Secure | Scalable | Smart")

# --- SESSION STATE SETUP ---
session_defaults = {
    "chat_history": [],
    "user_question": "",
    "feedback": [],
    "document_content": {},
    "document_summary": {},
    "uploaded_filenames": []
}
for key, default in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- TITLE ---
st.title("DeloitteSmart™: Your AI Assistant for Faster, Smarter Decisions")

# --- FILE UPLOAD ---
with st.expander("📁 Upload Documents (PDF, TXT)"):
    uploaded_files = st.file_uploader("Upload Files", type=["pdf", "txt"], accept_multiple_files=True)
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
                if openai_api_key:
                    try:
                        prompt = f"You are a highly trained consultant. Summarize the following content and generate 5 smart questions.\n\nDocument:\n{doc_text}"
                        response = openai.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are an AI assistant specialized in summarizing and extracting smart questions."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        st.session_state.document_summary[filename] = response.choices[0].message.content
                    except Exception as e:
                        st.error(f"Summary generation error for {filename}: {str(e)}")

# --- SHOW SUMMARIES ---
if st.session_state.document_summary:
    st.subheader("📄 Summaries & Smart Questions")
    for fname, summary in st.session_state.document_summary.items():
        st.markdown(f"**🗂️ {fname}**")
        st.markdown(summary)
        st.markdown("---")

# --- CAMERA INPUT temporarily removed ---
# --- CONTINUED QUESTION INPUT ---
combined_docs = "

".join(st.session_state.document_content.values())

st.subheader("💬 Ask Questions Based on Uploaded Documents")
with st.form("question_form"):
    user_input = st.text_input("Ask a question about your uploaded content:", key="user_input")
    submitted = st.form_submit_button("Ask")

    if submitted and user_input.strip():
        if not openai_api_key:
            st.warning("OpenAI API key not found.")
        elif not combined_docs:
            st.warning("Please upload documents or capture an image first.")
        else:
            try:
                qa_prompt = f"""
You are a helpful AI assistant designed to answer questions based on the following documents:

{combined_docs}

Question:
{user_input.strip()}
"""
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an AI assistant that answers questions based on uploaded documents."},
                        {"role": "user", "content": qa_prompt}
                    ]
                )
                reply = response.choices[0].message.content
                st.session_state.chat_history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "question": user_input.strip(),
                    "answer": reply
                })
                st.success("Answer generated and saved to history.")
            except Exception as e:
                st.error(f"AI response error: {str(e)}")

# --- DISPLAY CHAT HISTORY ---
if st.session_state.chat_history:
    st.markdown("---")
    st.subheader("📜 Conversation History")
    for chat in reversed(st.session_state.chat_history):
        st.markdown(f"**🧑‍💼 You ({chat['timestamp']}):** {chat['question']}")
        st.markdown(f"**🤖 AI:** {chat['answer']}")
        st.markdown("---")
