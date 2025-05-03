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

    elif mode == "Deloitte-Asks":
        st.subheader("Get Smart Questions to Ask Your Client")
        client_profile = st.text_area("Describe the client (industry, size, goal, etc.):")
        uploaded_file = st.file_uploader("Upload Client Business Overview (Optional - .txt file)", type=["txt"])
        with st.expander("📝 Optional: Score this client"):
            age = st.radio("Company age?", ["< 3 years", "≥ 3 years"], index=0)
            industry = st.multiselect("Industry?", ["AI","IT", "IoT", "Biotech", "Green Energy", "Other"])
            rd_budget = st.radio("R&D budget per year?", ["< $200K", "≥ $200K"], index=0)
            export_ready = st.radio("Exporting or planning to export?", ["No", "Yes"], index=0)
            revenue = st.radio("Annual revenue?", ["< $500K", "≥ $500K"], index=0)
            employees = st.slider("Number of employees?", 1, 200, 10)
            documents = st.multiselect("Documents provided", ["Business Plan","Trial Balance","Annual Return", "Org Chart", "Budget", "Export Plan", "Pitch Deck"])

        if st.button("Get AI Insights & Questions"):
            if not openai_api_key:
                st.error("API key missing.")
            elif not client_profile:
                st.warning("Please describe the client first.")
            else:
                openai.api_key = openai_api_key
                document_content = None
                if uploaded_file is not None:
                    document_content = uploaded_file.read().decode("utf-8")
                    st.write(f"📄 Analyzing document: {uploaded_file.name}") # Optional: Show filename

                prompt = f"""
            You are SubsidySmart™, a Deloitte-trained AI assistant with advanced document analysis capabilities. Your goal is to help Deloitte consultants quickly assess client subsidy eligibility.

            Analyze the following Client Profile and any provided Client Document Content to determine potential eligibility for Japanese government subsidies and suggest insightful follow-up questions. Also, recommend 1-2 specific subsidy programs with clear justifications based on the provided information.

            **Client Profile:**
            {client_profile}

            **Client Document Content:**
            {'[START DOCUMENT]' + document_content + '[END DOCUMENT]' if document_content else 'No client document provided.'}

            Consider the following potential programs and their key eligibility criteria:
            - **SME Business Expansion Grant 2025:** Supports SMEs (5-100 employees, <$50M revenue) for new market expansion. Look for keywords like "new market," "expansion," "growth," "overseas," etc.
            - **Technology Innovation Support Program 2025:** Funds R&D projects in AI, IoT, biotech, and green energy (3+ years operational history). Look for keywords like "research," "development," "innovation," "technology," and specific tech areas.
            - **Export Development Assistance 2025:** Supports export expansion (>$500K domestic sales). Look for keywords like "export," "international," "global," "marketing abroad," etc.

            Provide your recommendations and questions in a clear, concise format. Highlight the specific evidence from the Client Profile or Document Content that supports your suggestions.
            """
                with st.spinner("Getting AI Insights & Questions..."):
                    try:
                        response = openai.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are an expert Deloitte subsidy consultant analyzing client information to provide program recommendations and key questions."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        ai_response = response.choices[0].message.content
                        st.markdown("### AI Insights & Recommendations")
                        st.markdown(ai_response)
                        # --- (We'll integrate scoring later based on this response) ---
                    except OpenAIError as e:
if st.button("Get AI Insights & Questions"):

            if not openai_api_key:

                st.error("API key missing.")

            elif not client_profile:

                st.warning("Please describe the client first.")

            else:

                openai.api_key = openai_api_key

                document_content = None

                if uploaded_file is not None:

                    document_content = uploaded_file.read().decode("utf-8")

                    st.write(f"📄 Analyzing document: {uploaded_file.name}") # Optional: Show filename

                prompt = f"""

                You are SubsidySmart™, a Deloitte-trained AI assistant with advanced document analysis capabilities. Your goal is to help Deloitte consultants quickly assess client subsidy eligibility.

                Analyze the following Client Profile and any provided Client Document Content to determine potential eligibility for Japanese government subsidies and suggest insightful follow-up questions. Also, recommend 1-2 specific subsidy programs with clear justifications based on the provided information.

                **Client Profile:**

                {client_profile}


                **Client Document Content:**

                {'[START DOCUMENT]' + document_content + '[END DOCUMENT]' if document_content else 'No client document provided.'}

                Consider the following potential programs and their key eligibility criteria:

                - **SME Business Expansion Grant 2025:** Supports SMEs (5-100 employees, <$50M revenue) for new market expansion. Look for keywords like "new market," "expansion," "growth," "overseas," etc.

                - **Technology Innovation Support Program 2025:** Funds R&D projects in AI, IoT, biotech, and green energy (3+ years operational history). Look for keywords like "research," "development," "innovation," "technology," and specific tech areas.

                - **Export Development Assistance 2025:** Supports export expansion (>$500K domestic sales). Look for keywords like "export," "international," "global," "marketing abroad," etc.



                Provide your recommendations and questions in a clear, concise format. Highlight the specific evidence from the Client Profile or Document Content that supports your suggestions.

                """
                with st.spinner("Getting AI Insights & Questions..."):

                    try:

                        response = openai.chat.completions.create(

                            model="gpt-3.5-turbo",

                            messages=[

                                {"role": "system", "content": "You are an expert Deloitte subsidy consultant analyzing client information to provide program recommendations and key questions."},

                                {"role": "user", "content": prompt}

                            ]

                        )

                        ai_response = response.choices[0].message.content

                        st.markdown("### AI Insights & Recommendations")

                        st.markdown(ai_response)

                        st.session_state["initial_ai_response"] = ai_response # Store initial response

                    except OpenAIError as e:

                        st.error(f"OpenAI Error: {str(e)}")

        st.subheader("Ask Questions About the Document")

        followup_question = st.text_input("Type your question about the uploaded document here:")

        if st.button("Ask AI About Document"):

            if followup_question and uploaded_file:

                openai.api_key = openai_api_key

                question_prompt = f"""

                You are an AI assistant that can answer questions based on the following Client Profile and Client Document Content.

                **Client Profile:**

                {client_profile}


                **Client Document Content:**

                [START DOCUMENT]{document_content}[END DOCUMENT]

                Answer the following question based *only* on the information provided above:

                **Question:** {followup_question}

                """

                with st.spinner("Getting answer..."):

                    try:

                        response = openai.chat.completions.create(

                            model="gpt-3.5-turbo",

                            messages=[

                                {"role": "system", "content": "You are an AI assistant answering questions based on provided documents."},

                                {"role": "user", "content": question_prompt}

                            ]

                        )

                        answer = response.choices[0].message.content

                        st.markdown(f"**Question:** {followup_question}")

                        st.markdown(f"**Answer:** {answer}")

                    except OpenAIError as e:

                        st.error(f"OpenAI Error: {str(e)}")

            elif not uploaded_file:

                st.warning("Please upload a document first to ask questions about it.")

            elif not followup_question:

                st.warning("Please enter a question.")
                        st.error(f"OpenAI Error: {str(e)}")

    if st.session_state.chat_history:
        st.markdown("---")
        st.subheader("Conversation History")
        for chat in reversed(st.session_state.chat_history):
            with st.container():
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
    - Phase 3: CRM
    - Phase 4: Analytics Dashboard
    """)
