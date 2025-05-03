import streamlit as st
# --- CONFIG ---
st.set_page_config(
    page_title="DeloitteSmart™ - AI Assistant",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded"
)

import openai
from datetime import datetime
from openai import OpenAIError

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
                You are a highly experienced Deloitte consultant specializing in Japanese government subsidies, known for your meticulous analysis and clear communication. When answering the user's question, please follow a structured thought process:

                1. **Identify Relevant Subsidy Programs:** Based on the user's question and the provided context, determine which of the following subsidy programs are most likely to be relevant.
                   - SME Business Expansion Grant 2025: Supports SMEs with up to 50% of project costs for new market expansion. (Eligibility: 5-100 employees, <$50M revenue)
                   - Technology Innovation Support Program 2025: Funds up to 60% of R&D projects in AI, IoT, biotech, and green energy. (Eligibility: 3+ years operational history)
                   - Export Development Assistance 2025: Supports export expansion with 70% coverage for international marketing costs. (Eligibility: $500K+ domestic sales)

                2. **Analyze Eligibility Criteria:** For each potentially relevant program, briefly analyze if the user's question provides enough information to assess eligibility based on the stated criteria. Highlight any missing information that would be needed for a definitive assessment.

                3. **Provide a Concise Answer:** Based on your analysis, provide a clear and concise answer to the user's question, citing the most relevant subsidy program(s). If the information is insufficient for a definitive answer, explain what additional details are required.

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
                        # --- DEBUGGING ---
                        st.write(f"**DEBUG: Raw OpenAI Response:** {response}")
                        st.write(f"**DEBUG: AI Reply:** {reply}")
                        # --- END DEBUGGING ---
                        st.session_state.chat_history.append({
                            "question": user_question,
                            "answer": reply,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        st.success("✅ Answer generated below!")

                    except OpenAIError as e:
                        st.error(f"OpenAI API Error: {str(e)}")

    if st.session_state.chat_history:
        st.markdown("---")
        st.subheader("Conversation History")
        for chat in reversed(st.session_state.chat_history):
            with st.container():
                st.markdown(f"**🧑 You ({chat['timestamp']}):** {chat['question']}")
                st.markdown(f"**🤖 DeloitteSmart™:** {chat['answer']}")
                st.markdown("---")

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
                You are SubsidySmart™, a Deloitte-trained AI assistant. Based on the following client profile, generate a short list of key questions a Deloitte consultant should ask the client in order to assess eligibility for Japanese government subsidy programs. Group the questions by the relevant subsidy program.

                Client Profile:
                {client_profile}

                Consider the following potential programs:
                - SME Business Expansion Grant 2025 (Eligibility: 5-100 employees, <$50M revenue, new market expansion focus)
                - Technology Innovation Support Program 2025 (Eligibility: 3+ years operational history, R&D in AI, IoT, biotech, green energy)
                - Export Development Assistance 2025 (Eligibility: $500K+ domestic sales, export expansion plans)

                Return the questions in a clear, numbered format under each relevant subsidy program heading.
                """

                with st.spinner("Generating interview questions..."):
                    try:
                        response = openai.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are a professional Deloitte consultant creating effective client assessment questions for Japanese government subsidies."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        consultant_questions = response.choices[0].message.content
                        st.markdown("### Suggested Interview Questions")
                        st.markdown(consultant_questions)

                        # --- SCORING LOGIC WITH WEIGHTS AND BREAKDOWN ---
                        score = 0
                        score_breakdown = {}

                        # Weights (you can adjust these based on importance in Japan)
                        weights = {
                            "age": 15,
                            "industry": 20,
                            "rd_budget": 20,
                            "export_ready": 15,
                            "revenue": 10,
                            "employees": 10,
                            "documents": 2
                        }

                        if age == "≥ 3 years":
                            score += weights["age"]
                            score_breakdown["Company Age"] = weights["age"]
                        else:
                            score_breakdown["Company Age"] = 0

                        industry_points = 0
                        if any(i in ["AI", "IoT", "Biotech", "Green Energy"] for i in industry):
                            industry_points = weights["industry"]
                            score += industry_points
                        score_breakdown["Industry"] = industry_points

                        if rd_budget == "≥ $200K":
                            score += weights["rd_budget"]
                            score_breakdown["R&D Budget"] = weights["rd_budget"]
                        else:
                            score_breakdown["R&D Budget"] = 0

                        if export_ready == "Yes":
                            score += weights["export_ready"]
                            score_breakdown["Export Involvement"] = weights["export_ready"]
                        else:
                            score_breakdown["Export Involvement"] = 0

                        if revenue == "≥ $500K":
                            score += weights["revenue"]
                            score_breakdown["Annual Revenue"] = weights["revenue"]
                        else:
                            score_breakdown["Annual Revenue"] = 0

                        if 5 <= employees <= 100:
                            score += weights["employees"]
                            score_breakdown["Number of Employees"] = weights["employees"]
                        else:
                            score_breakdown["Number of Employees"] = 0

                        documents_points = len(documents) * weights["documents"]
                        score += documents_points
                        score_breakdown["Documents Provided"] = documents_points

                        st.markdown("### 🧮 Eligibility Score Breakdown")
                        for criterion, points in score_breakdown.items():
                            st.markdown(f"- **{criterion}:** {points} points")

                        st.metric("Total Score (%)", f"{score}%")

                        st.markdown("### 🚦 Eligibility Status")
                        if score >= 85:
                            st.success("🟢 Highly Eligible")
                            st.markdown("The client meets most of the key criteria and has a strong likelihood of eligibility.")
                        elif score >= 70:
                            st.warning("🟡 Likely Eligible, Needs Review")
                            st.markdown("The client meets a significant number of criteria but may need further review to confirm specific requirements.")
                        elif score >= 55:
                            st.warning("🟠 Potentially Eligible, Further Assessment Required")
                            st.markdown("The client meets some criteria, but a more detailed assessment is needed to determine eligibility and identify suitable programs.")
                        else:
                            st.error("🔴 Not Currently Eligible")
                            st.markdown("Based on the information provided, the client does not currently meet the key eligibility criteria for the considered programs.")

                    except OpenAIError as e:
                        st.error(f"OpenAI Error: {str(e)}")
