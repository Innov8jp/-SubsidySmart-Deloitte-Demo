
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

# --- SESSION STATE SETUP ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "user_question" not in st.session_state:
    st.session_state.user_question = ""

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

                        # ✅ Safely clear input and rerun
                        if "user_question" in st.session_state:
                            del st.session_state["user_question"]
                            st.experimental_rerun()

                    except OpenAIError as e:
                        st.error(f"OpenAI API Error: {str(e)}")

    elif mode == "Deloitte-Asks":
        st.subheader("Get Smart Questions to Ask Your Client")
        client_profile = st.text_area("Describe the client (industry, size, goal, etc.):", key="client_profile")
        uploaded_file = st.file_uploader("Upload Client Business Overview (Optional - .txt file)", type=["txt"], key="uploaded_file")

        document_content = None
        if uploaded_file:
            document_content = uploaded_file.read().decode("utf-8")
            st.markdown(f"📄 **Uploaded file:** {uploaded_file.name}")

        if st.button("Get AI Insights & Questions", key="insights_btn"):
            if not openai_api_key:
                st.error("API key missing.")
            elif not client_profile.strip():
                st.warning("Please describe the client first.")
            else:
                openai.api_key = openai_api_key
                prompt = f"""
You are SubsidySmart™, a highly intelligent Deloitte AI assistant. Your goal is to provide expert-level analysis of client profiles and documents to determine eligibility for Japanese government subsidies. Follow a structured reasoning process:

1. **Analyze Client Profile:** Identify key characteristics of the client (industry, size, goals, etc.).
2. **Analyze Client Document (if provided):** Extract key information related to their business activities, R&D, expansion plans, etc.
3. **Based on the analysis, consider the following Japanese subsidy programs and their core requirements:**
   - **SME Business Expansion Grant 2025:** Supports SMEs (5-100 employees, <$50M revenue) for new market expansion.
   - **Technology Innovation Support Program 2025:** Funds R&D in AI, IoT, biotech, green energy (3+ years operational history).
   - **Export Development Assistance 2025:** Supports export expansion (>$500K domestic sales).
4. **Recommend 1-2 most relevant subsidy programs.** For each recommendation, briefly explain *why* the client might be eligible based on the analyzed information.
5. **Formulate 2-3 insightful follow-up questions** a Deloitte consultant should ask the client to gather more specific details and confirm eligibility.

Present your output in a clear, structured format:

**AI Subsidy Assessment:**

**Recommended Programs:**
- [Program Name 1]: [Brief justification based on client info]
- [Program Name 2]: [Brief justification based on client info]

**Follow-Up Questions:**
- [Question 1]
- [Question 2]
- [Question 3]

**Client Profile:**
{client_profile}

**Client Document:**
{'[START DOCUMENT]' + document_content + '[END DOCUMENT]' if document_content else 'No document provided.'}
"""
                with st.spinner("Getting AI Insights & Questions..."):
                    try:
                        response = openai.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are an expert Deloitte subsidy consultant providing detailed eligibility assessments."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        ai_response = response.choices[0].message.content
                        st.markdown("### AI Insights & Recommendations")
                        st.markdown(ai_response)
                        st.session_state["initial_ai_response"] = ai_response

                    except OpenAIError as e:
                        st.error(f"OpenAI Error: {str(e)}")

        if uploaded_file:
            st.subheader("Ask Questions About the Document")
            followup_question = st.text_input("Type your question about the uploaded document here:", key="followup_question")
            if st.button("Ask AI About Document", key="followup_btn"):
                if followup_question:
                    question_prompt = f"""
You are an AI assistant. Based ONLY on the following:

Client Profile:
{client_profile}

Client Document:
{document_content}

Answer this question:
{followup_question}
"""
                    with st.spinner("Getting answer..."):
                        try:
                            response = openai.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[
                                    {"role": "system", "content": "You are an AI assistant answering based on documents."},
                                    {"role": "user", "content": question_prompt}
                                ]
                            )
                            answer = response.choices[0].message.content
                            st.markdown(f"**Question:** {followup_question}")
                            st.markdown(f"**Answer:** {answer}")
                        except OpenAIError as e:
                            st.error(f"OpenAI Error: {str(e)}")
                else:
                    st.warning("Please enter a question.")

    # --- Optional: Reset Chat Button ---
    if st.session_state.chat_history:
        if st.button("🔁 Reset Chat"):
            st.session_state.chat_history = []
            st.success("Chat history cleared.")
            st.experimental_rerun()

    # --- Display Chat History ---
    if st.session_state.chat_history:
        st.markdown("---")
        st.subheader("Conversation History")
        for chat in reversed(st.session_state.chat_history):
            with st.container():
                st.markdown(f"**🧑 You ({chat['timestamp']}):** {chat['question']}")
                st.markdown(f"**🤖 DeloitteSmart™:** {chat['answer']}")
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
