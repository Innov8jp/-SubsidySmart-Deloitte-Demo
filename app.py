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

# --- SESSION STATE SETUP ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "user_question" not in st.session_state:
    st.session_state.user_question = ""
if "feedback" not in st.session_state:
    st.session_state.feedback = []
if "show_feedback" not in st.session_state:
    st.session_state.show_feedback = False

# --- MAIN PAGE ---
st.title("DeloitteSmart™: Your AI Assistant for Faster, Smarter Decisions")
st.caption("より速く、よりスマートな意思決定のためのAIアシスタント")
st.caption("Ask any business subsidy question and get instant expert advice, powered by Deloitte AI Agent.")

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
                prompt = f"""
You are a highly experienced Deloitte consultant specializing in Japanese government subsidies. Use a structured thought process:

1. Identify relevant subsidy programs (3 listed).
2. Analyze user eligibility based on the question.
3. Provide a concise, professional answer. If needed, request missing info.

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

                    except OpenAIError as e:
                        st.error(f"OpenAI API Error: {str(e)}")

    elif mode == "Deloitte-Asks":
        st.subheader("Get Smart Questions to Ask Your Client")
        client_profile = st.text_area("Describe the client (industry, size, goal, etc.):", key="client_profile")
        uploaded_files = st.file_uploader("Upload Client Business Overview(s) (.txt or .pdf)", type=["txt", "pdf"], accept_multiple_files=True)
        enable_camera = st.checkbox("📷 Enable Camera Input")

        captured_image = None
        if enable_camera:
            captured_image = st.camera_input("Take a picture of the document (Optional)")

        document_content = ""
        if uploaded_files:
            for file in uploaded_files:
                file_type = file.type
                if file_type == "application/pdf":
                    pdf = fitz.open(stream=file.read(), filetype="pdf")
                    for page in pdf:
                        document_content += page.get_text()
                else:
                    content = file.read().decode("utf-8")
                    document_content += f"\n\n--- FILE: {file.name} ---\n{content}"

        if st.button("Get AI Insights & Questions", key="insights_btn"):
            if not openai_api_key:
                st.error("API key missing.")
            elif not client_profile.strip():
                st.warning("Please describe the client first.")
            else:
                openai.api_key = openai_api_key
                prompt = f"""
You are SubsidySmart™, a Deloitte-trained AI assistant. Analyze the profile below and extract key information. Based on that, recommend relevant Japanese subsidy programs and insightful follow-up questions.

Client Profile:
{client_profile}

Client Documents:
{document_content if document_content else 'No document provided.'}
"""
                with st.spinner("Getting AI Insights & Questions..."):
                    try:
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
                        st.session_state.show_feedback = True
                        st.session_state.chat_history.append({
                            "question": client_profile,
                            "answer": ai_response,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        with open("chat_feedback_log.json", "a", encoding="utf-8") as f:
                            f.write(json.dumps(st.session_state.chat_history[-1]) + "\n")
                    except OpenAIError as e:
                        st.error(f"OpenAI Error: {str(e)}")

# --- FEEDBACK ---
if st.session_state.get("show_feedback") and st.session_state.chat_history:
    latest = len(st.session_state.chat_history) - 1
    st.markdown(st.session_state.chat_history[latest]["answer"])
    st.write("**Was this helpful?**")
    col_yes, col_no = st.columns([1, 1])
    with col_yes:
        if st.button("👍 Yes", key="yes_feedback"):
            feedback_entry = {"index": latest, "helpful": True, "timestamp": datetime.now().isoformat()}
            st.session_state.feedback.append(feedback_entry)
            with open("feedback_log.json", "a", encoding="utf-8") as f:
                f.write(json.dumps(feedback_entry) + "\n")
            st.session_state.show_feedback = False
            st.success("Thank you for your feedback!")
            st.rerun()
    with col_no:
        if st.button("👎 No", key="no_feedback"):
            feedback_entry = {"index": latest, "helpful": False, "timestamp": datetime.now().isoformat()}
            st.session_state.feedback.append(feedback_entry)
            with open("feedback_log.json", "a", encoding="utf-8") as f:
                f.write(json.dumps(feedback_entry) + "\n")
            st.session_state.show_feedback = False
            st.info("Feedback noted. We'll use it to improve.")
            st.rerun()

# --- Chat History Display ---
if st.session_state.chat_history:
    st.markdown("---")
    st.subheader("Conversation History")
    for i, chat in enumerate(reversed(st.session_state.chat_history)):
        with st.container():
            st.markdown(f"**🧑‍💻 You ({chat['timestamp']}):** {chat['question']}")
            st.markdown(f"**🤖 DeloitteSmart™:** {chat['answer']}")
            fb = next((f for f in st.session_state.feedback if f['index'] == len(st.session_state.chat_history)-1-i), None)
            if fb:
                st.caption("📊 Feedback: Helpful" if fb['helpful'] else "📊 Feedback: Not Helpful")
            st.markdown("---")

    col_reset, col_download = st.columns([1, 1])
    with col_reset:
        if st.button("🔁 Reset Chat"):
            st.session_state.chat_history = []
            st.session_state.feedback = []
            st.success("Chat history cleared.")
            st.rerun()
    with col_download:
        chat_json = json.dumps(st.session_state.chat_history, indent=2)
        st.download_button(
            label="📥 Download Chat History",
            data=chat_json,
            file_name="chat_history.json",
            mime="application/json"
        )

# --- RIGHT COLUMN ---
with col2:
    st.subheader("ℹ️ Assistant Overview")
    st.markdown("""
✅ Real-time subsidy advice  
✅ Smart scoring system  
✅ Ready for CRM + Drafting  
""")
    st.subheader("📈 Deloitte Roadmap")
    st.markdown("""
- Phase 1: Internal AI Assistant  
- Phase 2: Client Portal  
- Phase 3: CRM  
- Phase 4: Analytics Dashboard  
""")
