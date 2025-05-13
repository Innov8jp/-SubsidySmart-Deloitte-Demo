# DeloitteSmart™ AI Assistant (Updated with PDF & Multi-Question Support)

import streamlit as st
import openai
import fitz  # PyMuPDF
import io
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

# --- SIDEBAR ---
with st.sidebar:
    st.image("deloitte_logo.png", width=200)
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    st.markdown("✅ OpenAI API key is pre-configured.")
    st.markdown("Powered by [Innov8]")
    st.markdown("Prototype Version 1.0")
    st.markdown("Secure | Scalable | Smart")
    with st.expander("📊 Feedback Analytics"):
        if os.path.exists("feedback_log.json"):
            with open("feedback_log.json", "r", encoding="utf-8") as f:
                feedback_data = [json.loads(line) for line in f.readlines()]

            total_feedback = len(feedback_data)
            helpful_count = sum(1 for f in feedback_data if f["helpful"])
            not_helpful_count = total_feedback - helpful_count

            st.metric("Total Feedback", total_feedback)
            st.metric("👍 Helpful", helpful_count)
            st.metric("👎 Not Helpful", not_helpful_count)
            st.progress(helpful_count / total_feedback if total_feedback else 0)
        else:
            st.info("No feedback data available yet.")

# --- SESSION STATE SETUP ---
for key in ["chat_history", "user_question", "feedback", "show_feedback", "enable_camera"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key in ["chat_history", "feedback"] else False

if "document_content" not in st.session_state:
    st.session_state.document_content = ""

# --- FILE UPLOAD AND DOCUMENT PARSING ---
uploaded_files = st.file_uploader("Upload Documents (PDF, TXT)", type=["pdf", "txt"], accept_multiple_files=True)

# Only re-parse if new files uploaded
if uploaded_files:
    doc_text = ""
    for file in uploaded_files:
        if file.type == "application/pdf":
            with fitz.open(stream=file.read(), filetype="pdf") as doc:
                for page in doc:
                    doc_text += page.get_text()
        elif file.type == "text/plain":
            doc_text += file.read().decode("utf-8")
    st.session_state.document_content = doc_text  # ✅ Save in session

# --- MAIN PAGE ---
st.title("DeloitteSmart™: Your AI Assistant for Faster, Smarter Decisions")
st.caption("より速く、よりスマートな意思決定のためのAIアシスタント")
st.caption("Ask any business domain specific question and get instant expert advice, powered by Deloitte AI Agent.")

mode = st.radio("Choose interaction mode:", ["Client-Asks (Default)", "Deloitte-Asks"], index=0)
col1, col2 = st.columns([3, 1])

# --- LEFT COLUMN ---
with col1:
    if mode == "Client-Asks (Default)":
        st.subheader("Ask Your Question")
        st.text_input("Type your subsidy-related question here:", key="user_question")

        if st.button("Ask Deloitte AI Agent™"):
            user_question = st.session_state.user_question.strip()

            if not openai_api_key:
                st.error("API key missing.")
            elif not user_question:
                st.warning("Please enter a question.")
            else:
                openai.api_key = openai_api_key
                context = st.session_state.get("document_content", "No document uploaded.")
                prompt = f"""
You are a highly experienced Deloitte consultant specializing in Japanese government subsidies.

Use the following context (if any) and the user's question to respond precisely:

Context Document:
{context}

User Question: {user_question}
"""
                with st.spinner("Analyzing with DeloitteSmart™..."):
                    try:
                        response = openai.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are a highly experienced Deloitte consultant specializing in Japanese government subsidies."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        reply = response.choices[0].message.content
                        entry = {
                            "question": user_question,
                            "answer": reply,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        st.session_state.chat_history.append(entry)
                        st.session_state.show_feedback = True

                        with open("chat_feedback_log.json", "a", encoding="utf-8") as f:
                            f.write(json.dumps(entry) + "\n")

                        st.success("✅ Answer generated below!")
                        st.markdown(reply)

                    except OpenAIError as e:
                        st.error(f"OpenAI API Error: {str(e)}")

# --- (rest of the Deloitte-Asks logic and UI elements remain unchanged) ---
# (as needed, you can carry over other blocks of logic from the previous version or let me know if you'd like it included as well)
