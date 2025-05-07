import streamlit as st
import openai
import fitz  # PyMuPDF
import io
import json
from datetime import datetime
from openai import OpenAIError

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
                        st.session_state.chat_history.append({
                            "question": user_question,
                            "answer": reply,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        st.success("✅ Answer generated below!")
                        st.markdown(reply)

                        # Feedback buttons
                        feedback_col1, feedback_col2 = st.columns([1, 1])
                        with feedback_col1:
                            if st.button("👍 Yes", key=f"yes_{len(st.session_state.chat_history)}"):
                                st.session_state.feedback.append({"index": len(st.session_state.chat_history)-1, "helpful": True})
                                st.success("Thank you for your feedback!")
                        with feedback_col2:
                            if st.button("👎 No", key=f"no_{len(st.session_state.chat_history)}"):
                                st.session_state.feedback.append({"index": len(st.session_state.chat_history)-1, "helpful": False})
                                st.info("Feedback noted. We'll use it to improve.")

                        if "user_question" in st.session_state:
                            del st.session_state.user_question
                        st.rerun()

                    except OpenAIError as e:
                        st.error(f"OpenAI API Error: {str(e)}")

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
