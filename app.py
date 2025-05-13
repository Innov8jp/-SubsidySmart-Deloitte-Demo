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

# --- CAMERA INPUT (Demo Version) ---
st.subheader("📸 Capture Image for Testing (Demo Only)")
captured_image = st.camera_input("Take a picture")
if captured_image:
    st.image(captured_image, caption="Captured Image", use_column_width=True)
    st.info("✅ Image captured. In this demo version, OCR is not applied.")
    dummy_text = "Thank you for uploading a photo. In the full version, text would be extracted and summarized here."
    cam_doc_name = f"camera_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    st.session_state.document_content[cam_doc_name] = dummy_text
    st.session_state.document_summary[cam_doc_name] = """**Demo Summary**: This is where the summary of the captured document would appear.

**Smart Questions:**
1. What is the document about?
2. Who is the target audience?
3. What actions are recommended?
4. Is any regulatory compliance mentioned?
5. What funding or budget is required?"""
    st.session_state.uploaded_filenames.append(cam_doc_name)
    st.success("✅ Demo summary and questions have been added from captured image.")
# --- RADIO OPTION FOR MODE ---
mode = st.radio("Choose interaction mode:", ["Client-Asks (Default)", "Deloitte-Asks"], index=0)

if mode == "Client-Asks (Default)":
    st.subheader("Ask Your Question")
    with st.form("chat_input_form", clear_on_submit=True):
        col1, col2 = st.columns([9, 1])
        with col1:
            user_input = st.text_input("Ask anything about the uploaded documents...", key="user_input")
        with col2:
            st.markdown("<div>&nbsp;</div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Ask", use_container_width=True)

        if submitted and user_input:
            all_text = "

".join(st.session_state.document_content.values())
            if not all_text.strip():
                st.warning("Please upload documents before asking questions.")
            elif not openai_api_key:
                st.warning("OpenAI API key is not available. Cannot answer questions.")
            else:
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                try:
                    prompt = f"You are a helpful AI assistant designed to answer questions based on the provided documents.

Documents:
{all_text}

Question: {user_input}"
                    response = openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are an AI assistant that answers questions based on provided documents."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    reply = response.choices[0].message.content
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    st.success("✅ Answer generated below!")
                    st.markdown(reply)
                except OpenAIError as e:
                    st.error(f"OpenAI API Error: {str(e)}")

elif mode == "Deloitte-Asks":
    st.subheader("Get Smart Questions to Ask Your Client")
    client_profile = st.text_area("Describe the client (industry, size, goal, etc.):", key="client_profile")
    uploaded_file = st.file_uploader("Upload Client Business Overview (Optional - .txt file)", type=["txt"])

    document_content = uploaded_file.read().decode("utf-8") if uploaded_file else "No document provided."

    if st.button("Get AI Insights & Questions", key="insights_btn"):
        if not openai_api_key:
            st.error("API key missing.")
        elif not client_profile.strip():
            st.warning("Please describe the client first.")
        else:
            try:
                prompt = f"You are an AI assistant analyzing client profiles and business plans to recommend subsidy programs and suggest follow-up questions.

Client Profile:
{client_profile}

Client Document:
{document_content}"
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a Deloitte subsidy expert."},
                        {"role": "user", "content": prompt}
                    ]
                )
                ai_response = response.choices[0].message.content
                st.markdown("### AI Insights & Recommendations")
                st.markdown(ai_response)
            except OpenAIError as e:
                st.error(f"OpenAI Error: {str(e)}")


# --- DOWNLOAD CHAT REPORT ---
if st.session_state.chat_history and st.session_state.document_summary:
    report_text = "# DeloitteSmart™ AI Assistant Report

## Document Summaries:
"
    for fname, summary in st.session_state.document_summary.items():
        report_text += f"### {fname}
{summary}

"
    report_text += "
## Chat History:
"
    for chat in st.session_state.chat_history:
        role = chat.get("role", "User").capitalize()
        content = chat.get("content", "")
        timestamp = chat.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        report_text += f"**{role} ({timestamp}):** {content}

"

    from io import BytesIO
    import base64

    def create_download_link(report):
        buffer = BytesIO()
        buffer.write(report.encode("utf-8"))
        buffer.seek(0)
        b64 = base64.b64encode(buffer.getvalue()).decode()
        href = f'data:text/plain;base64,{b64}'
        filename = f"deloitte_smart_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        return f'<a href="{href}" download="{filename}">📄 Download Full Report</a>'

    st.markdown("---")
    st.subheader("⬇️ Download Full Chat Report")
    st.markdown(create_download_link(report_text), unsafe_allow_html=True)

