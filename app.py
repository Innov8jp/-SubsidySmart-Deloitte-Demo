import streamlit as st
import openai
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

# --- MAIN PAGE ---
st.title("DeloitteSmart™: Your AI Assistant for Faster, Smarter Decisions")
st.caption("より速く、よりスマートな意思決定のためのAIアシスタント")
st.caption("Ask any business subsidy question and get instant expert advice, powered by Deloitte AI Agent.")

mode = st.radio("Choose interaction mode:", ["Client-Asks (Default)", "Deloitte-Asks"], index=0)
col1, col2 = st.columns([3, 1])

with col1:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # ✅ Input persistence
    if "user_question" not in st.session_state:
        st.session_state.user_question = ""

    if mode == "Client-Asks (Default)":
        st.subheader("Ask Your Question")
        user_question = st.text_input("Type your subsidy-related question here:", key="user_question")

        if st.button("Ask Deloitte AI Agent™"):
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

                        # ✅ Clear input
                        st.session_state.user_question = ""

                    except OpenAIError as e:
                        st.error(f"OpenAI API Error: {str(e)}")

    elif mode == "Deloitte-Asks":
        st.subheader("Get Smart Questions to Ask Your Client")
        client_profile = st.text_area("Describe the client (industry, size, goal, etc.):")
        uploaded_file = st.file_uploader("Upload Client Business Overview (Optional - .txt file)", type=["txt"])

        with st.expander("📝 Optional: Score this client"):
            st.radio("Company age?", ["< 3 years", "≥ 3 years"], index=0)
            st.multiselect("Industry?", ["AI","IT", "IoT", "Biotech", "Green Energy", "Other"])
            st.radio("R&D budget per year?", ["< $200K", "≥ $200K"], index=0)
            st.radio("Exporting or planning to export?", ["No", "Yes"], index=0)
            st.radio("Annual revenue?", ["< $500K", "≥ $500K"], index=0)
            st.slider("Number of employees?", 1, 200, 10)
            st.multiselect("Documents provided", ["Business Plan","Trial Balance","Annual Return", "Org Chart", "Budget", "Export Plan", "Pitch Deck"])

        document_content = None
        if uploaded_file:
            document_content = uploaded_file.read().decode("utf-8")
            st.write(f"📄 Uploaded: {uploaded_file.name}")

        if st.button("Get AI Insights & Questions"):
            if not openai_api_key:
                st.error("API key missing.")
            elif not client_profile:
                st.warning("Please describe the client first.")
            else:
                openai.api_key = openai_api_key
                prompt = f"""
You are SubsidySmart™, a Deloitte-trained AI assistant. Analyze the client profile and document to:
1. Suggest 1–2 relevant subsidy programs.
2. Justify eligibility.
3. Recommend smart questions to ask the client.

Client Profile:
{client_profile}

Client Document:
{document_content if document_content else 'No document uploaded.'}
"""
                with st.spinner("Getting AI Insights & Questions..."):
                    try:
