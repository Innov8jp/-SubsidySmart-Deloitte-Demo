import streamlit as st
import openai
from datetime import datetime
from openai import OpenAIError

# === MUST BE FIRST COMMAND ===
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

    if mode == "Client-Asks (Default)":
        st.subheader("Ask Your Question")
        user_question = st.text_input("Type your subsidy-related question here:")

        if st.button("Ask Deloitte AI Agent™"):
            if not openai_api_key:
                st.error("API key missing.")
            elif not user_question:
                st.warning("Please enter a question.")
            else:
                openai.api_key = openai_api_key
                prompt = f"""
                You are a highly experienced Deloitte consultant specializing in Japanese government subsidies.

                1. Identify relevant programs:
                   - SME Business Expansion Grant 2025
                   - Technology Innovation Support Program 2025
                   - Export Development Assistance 2025

                2. Assess eligibility based on info.
                3. Respond concisely, asking for more info if needed.

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

                    except OpenAIError as e:
                        st.error(f"OpenAI API Error: {str(e)}")

    elif mode == "Deloitte-Asks":
        st.subheader("Get Smart Questions to Ask Your Client")
        client_profile = st.text_area("Describe the client (industry, size, goal, etc.):")

        with st.expander("📝 Optional: Score this client"):
            age = st.radio("Company age?", ["< 3 years", "≥ 3 years"], index=0)
            industry = st.multiselect("Industry?", ["AI", "IoT", "Biotech", "Green Energy", "Other"])
            rd_budget = st.radio("R&D budget per year?", ["< $200K", "≥ $200K"], index=0)
            export_ready = st.radio("Exporting or planning to export?", ["No", "Yes"], index=0)
            revenue = st.radio("Annual revenue?", ["< $500K", "≥ $500K"], index=0)
            employees = st.slider("Number of employees?", 1, 200, 10)
            documents = st.multiselect("Documents provided", ["Business Plan", "Org Chart", "Budget", "Export Plan", "Pitch Deck"])

        if st.button("Generate Consultant Questions"):
            if not openai_api_key:
                st.error("API key missing.")
            elif not client_profile:
                st.warning("Please describe the client first.")
            else:
                openai.api_key = openai_api_key
                prompt = f"""
                You are SubsidySmart™, a Deloitte-trained AI assistant. Generate key questions for assessing eligibility based on:
                - SME Business Expansion Grant 2025
                - Technology Innovation Support Program 2025
                - Export Development Assistance 2025

                Client Profile:
                {client_profile}
                """

                with st.spinner("Generating questions..."):
                    try:
                        response = openai.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are a professional Deloitte consultant creating client assessment questions."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        consultant_questions = response.choices[0].message.content
                        st.markdown("### Suggested Interview Questions")
                        st.markdown(consultant_questions)

                        score = 0
                        weights = {"age":15, "industry":20, "rd":20, "export":15, "rev":10, "emp":10, "docs":2}
                        if age == "≥ 3 years": score += weights["age"]
                        if any(i in ["AI", "IoT", "Biotech", "Green Energy"] for i in industry): score += weights["industry"]
                        if rd_budget == "≥ $200K": score += weights["rd"]
                        if export_ready == "Yes": score += weights["export"]
                        if revenue == "≥ $500K": score += weights["rev"]
                        if 5 <= employees <= 100: score += weights["emp"]
                        score += len(documents) * weights["docs"]

                        st.metric("Eligibility Score", f"{score}%")
                        if score >= 85: st.success("🟢 Highly Eligible")
                        elif score >= 70: st.warning("🔒 Likely Eligible - Needs Review")
                        else: st.error("🔴 Not Currently Eligible")

                    except OpenAIError as e:
                        st.error(f"OpenAI Error: {str(e)}")

    if st.session_state.chat_history:
        st.markdown("---")
        st.subheader("Conversation History")
        for chat in reversed(st.session_state.chat_history):
            st.markdown(f"**🧑 You ({chat['timestamp']}):** {chat['question']}")
            st.markdown(f"**🤖 DeloitteSmart™:** {chat['answer']}")
            st.markdown("---")

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
    - Phase 3: CRM + Auto Drafts  
    - Phase 4: Analytics Dashboard
    """)
