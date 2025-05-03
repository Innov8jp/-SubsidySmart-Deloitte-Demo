import streamlit as st
import openai
from datetime import datetime

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

# --- Mode Toggle ---
mode = st.radio("Choose interaction mode:", ["Client-Asks (Default)", "Deloitte-Asks"], index=0)

col1, col2 = st.columns([3, 1])

with col1:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if mode == "Client-Asks (Default)":
        st.subheader("Ask Your Question")
        user_question = st.text_input("Type your subsidy-related question here:", key="input")

        if st.button("Ask Deloitte AI Agent™"):
            if not openai_api_key:
                st.error("Please enter your OpenAI API Key in the sidebar.")
            elif not user_question:
                st.warning("Please type a question first.")
            else:
                openai.api_key = openai_api_key
                prompt = f"""
                You are SubsidySmart™, an expert AI agent assisting Deloitte consultants and their clients in finding appropriate government subsidy programs based on their business situation.

                Context Documents:
                1. SME Business Expansion Grant 2025: Supports SMEs with up to 50% of project costs for new market expansion. (Eligibility: 5-100 employees, <$50M revenue)
                2. Technology Innovation Support Program 2025: Funds up to 60% of R&D projects in AI, IoT, biotech, and green energy. (Eligibility: 3+ years operational history)
                3. Export Development Assistance 2025: Supports export expansion with 70% coverage for international marketing costs. (Eligibility: $500K+ domestic sales)

                Please answer the user's question based on these programs only. Be clear, concise, and cite the matching program.

                User Question: {user_question}
                """

                with st.spinner("SubsidySmart™ is analyzing your question..."):
                    response = openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a professional and helpful government subsidy advisor."},
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

    elif mode == "Deloitte-Asks":
        st.subheader("Get Smart Questions to Ask Your Client")
        client_profile = st.text_area("Describe the client (industry, size, goal, etc.):", key="consult_input")

        with st.expander("📝 Optional: Score this client"):
            age = st.radio("Company age?", ["< 3 years", "≥ 3 years"], index=0)
            industry = st.multiselect("Industry?", ["AI", "IoT", "Biotech", "Green Energy", "Other"])
            rd_budget = st.radio("R&D budget per year?", ["< $200K", "≥ $200K"], index=0)
            export_ready = st.radio("Exporting or planning to export?", ["No", "Yes"], index=0)
            revenue = st.radio("Annual revenue?", ["< $500K", "≥ $500K"], index=0)
            employees = st.slider("Number of employees?", 1, 200, 10)
            documents = st.multiselect(
                "Documents provided",
                ["Business Plan", "Org Chart", "Budget", "Export Plan", "Pitch Deck"]
            )

        if st.button("Generate Consultant Questions"):
            if not openai_api_key:
                st.error("API key missing")
            elif not client_profile:
                st.warning("Please describe the client first.")
            else:
                openai.api_key = openai_api_key
                prompt = f"""
                You are SubsidySmart™, a Deloitte-trained AI assistant. Based on the following client profile, generate a short list of key questions a Deloitte consultant should ask the client in order to assess eligibility for government subsidy programs.

                Client Profile:
                {client_profile}

                Return the questions in a clear, numbered format, grouped by subsidy type (e.g., SME Expansion, R&D, Export).
                """

                with st.spinner("SubsidySmart™ is preparing your interview questions..."):
                    response = openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a professional Deloitte consultant creating effective client assessment questions."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    consultant_questions = response.choices[0].message.content
                    st.markdown("### Suggested Interview Questions")
                    st.markdown(consultant_questions)

                    # === Scoring Logic ===
                    score = 0
                    if age == "≥ 3 years":
                        score += 15
                    if any(i in ["AI", "IoT", "Biotech", "Green Energy"] for i in industry):
                        score += 20
                    if rd_budget == "≥ $200K":
                        score += 20
                    if export_ready == "Yes":
                        score += 15
                    if revenue == "≥ $500K":
                        score += 10
                    if 5 <= employees <= 100:
                        score += 10
                    score += len(documents) * 2  # 2% per document

                    st.markdown("### 🧮 Eligibility Score")
                    st.metric("Score (%)", f"{score}%")

                    if score >= 85:
                        st.success("🟢 Highly Eligible")
                    elif score >= 65:
                        st.warning("🔏 Potentially Eligible — Requires Review")
                    else:
                        st.error("🔴 Low Eligibility or Incomplete")

    if st.session_state.chat_history:
        st.markdown("---")
        st.subheader("Conversation History")
        for chat in reversed(st.session_state.chat_history):
            with st.container():
                st.markdown(f"**🧑 You ({chat['timestamp']}):** {chat['question']}")
                st.markdown(f"**🤖 DeloitteSmart™:** {chat['answer']}")
                st.markdown("---")

with col2:
    st.subheader("ℹ️ Information")
    st.markdown("""
    🧾 What This Assistant Can Do

    ✅ Answers questions about SME, R&D, and Export funding  
    ✅ Uses real, official government program documents  
    ✅ Built for future scaling — client portal, CRM, auto-drafts  
    ✅ Runs on a secure and flexible architecture
    """)
    st.subheader("📈 Roadmap")
    st.markdown("""
    - Phase 1: Consultant Use (Today)  
    - Phase 2: Client Portal  
    - Phase 3: Auto Application Drafts  
    - Phase 4: CRM Integration
    """)
