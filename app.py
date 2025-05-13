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
    st.subheader("🔍 Ask More Questions About the Documents")
    question_input = st.text_input("Your follow-up question:", placeholder="e.g., Which subsidy fits best for export growth?", key="user_question_input")
    if st.button("Ask AI"):
        question = question_input.strip()
        if question:
            openai.api_key = openai_api_key
            all_docs_combined = "\n\n".join(st.session_state.document_content.values())
            prompt = f"""
Refer to the following uploaded documents and answer the question below:

Document Content:
{all_docs_combined}

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
                entry = {
                    "question": question,
                    "answer": reply,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.chat_history.append(entry)
                st.session_state.show_feedback = True
                # Note: Resetting input this way causes a Streamlit error. Removing to avoid conflict.
            except Exception as e:
                st.error(f"AI response error: {str(e)}")

# --- DISPLAY CHAT HISTORY ---
if st.session_state.chat_history:
    st.markdown("---")
    st.subheader("🗂️ Conversation History")
    for i, chat in enumerate(reversed(st.session_state.chat_history)):
        st.markdown(f"**You ({chat['timestamp']}):** {chat['question']}")
        st.markdown(f"**AI:** {chat['answer']}")
        regenerate_key = f"regen_{i}"
        if st.button("🔄 Regenerate Answer", key=regenerate_key):
            try:
                openai.api_key = openai_api_key
                combined_docs = "\n\n".join(st.session_state.document_content.values())
                regen_prompt = f"""
Refer to the following uploaded documents and regenerate a better response to the question below:

Document Content:
{combined_docs}

User Question:
{chat['question']}
"""
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a Deloitte AI assistant."},
                        {"role": "user", "content": regen_prompt}
                    ]
                )
                regenerated_reply = response.choices[0].message.content
                st.session_state.chat_history[-(i+1)]["answer"] = regenerated_reply
                st.session_state.user_question_input = ""
                st.success("✅ Answer regenerated.")
            except Exception as e:
                st.error(f"Regeneration error: {str(e)}")
        st.markdown("---")

# --- DOWNLOAD REPORT ---
if st.session_state.document_summary:
    full_report = f"Summary and Smart Questions Generated on {datetime.now().strftime('%Y-%m-%d')}\n\n"
    for fname, summary in st.session_state.document_summary.items():
        full_report += f"\n--- {fname} ---\n{summary}\n"
    full_report += "\n--- Conversation History ---\n"
    for item in st.session_state.chat_history:
        full_report += f"\n[{item['timestamp']}]\nQ: {item['question']}\nA: {item['answer']}\n"
    st.download_button("📥 Download Report", full_report, file_name="deloitte_ai_summary.txt")

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
