import streamlit as st
import openai
from datetime import datetime
from openai import OpenAIError
import fitz  # PyMuPDF for PDF parsing

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

# --- SESSION STATE ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "user_question" not in st.session_state:
    st.session_state.user_question = ""

# --- MAIN PAGE HEADER ---
st.title("DeloitteSmart™: Your AI Assistant for Faster, Smarter Decisions")
st.caption("より速く、よりスマートな意思決定のためのAIアシスタント")
st.caption("Ask any business subsidy question and get instant expert advice, powered by Deloitte AI Agent.")

mode = st.radio("Choose interaction mode:", ["Client-Asks (Default)", "Deloitte-Asks"], index=0)
col1, col2 = st.columns([3, 1])

# --- LEFT PANEL ---
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
                        del st.session_state["user_question"]
                        st.experimental_rerun()
                    except OpenAIError as e:
                        st.error(f"OpenAI API Error: {str(e)}")

    elif mode == "Deloitte-Asks":
        st.subheader("Get Smart Questions to Ask Your Client")
        client_profile = st.text_area("Describe the client (industry, size, goal, etc.):")
        uploaded_files = st.file_uploader(
            "Upload Client Business Overview(s) (.txt or .pdf)", 
            type=["txt", "pdf"], 
            accept_multiple_files=True
        )
        captured_image = st.camera_input("Take a picture of the document (Optional)")

        document_content = ""
        if uploaded_files:
            for file in uploaded_files:
                if file.name.endswith(".pdf"):
                    pdf = fitz.open(stream=file.read(), filetype="pdf")
                    text = "\n".join([page.get_text() for page in pdf])
                else:
                    text = file.read().decode("utf-8")
                document_content += f"\n\n--- FILE: {file.name} ---\n{text}"

            st.markdown("📄 **Uploaded Files:**")
            for file in uploaded_files:
                st.markdown(f"- {file.name}")

        with st.expander("📝 Optional: Score this client"):
            st.radio("Company age?", ["< 3 years", "≥ 3 years"])
            st.multiselect("Industry?", ["AI", "IT", "IoT", "Biotech", "Green Energy", "Other"])
            st.radio("R&D budget per year?", ["< $200K", "≥ $200K"])
            st.radio("Exporting or planning to export?", ["No", "Yes"])
            st.radio("Annual revenue?", ["< $500K", "≥ $500K"])
            st.slider("Number of employees?", 1, 200, 10)
            st.multiselect("Documents provided", [
                "Business Plan", "Trial Balance", "Annual Return", 
                "Org Chart", "Budget", "Export Plan", "Pitch Deck"
            ])

        if st.button("Get AI Insights & Questions"):
            if not openai_api_key:
                st.error("API key missing.")
            elif not client_profile.strip():
                st.warning("Please describe the client first.")
            else:
                openai.api_key = openai_api_key
                prompt = f"""
You are SubsidySmart™, a Deloitte-trained AI assistant. Analyze the client profile and document to:
1. Suggest 1–2 relevant subsidy programs.
2. Justify eligibility.
3. Recommend 2-3 follow-up questions.

Client Profile:
{client_profile}

Client Document:
{'[START DOCUMENT]' + document_content + '[END DOCUMENT]' if document_content else 'No document provided.'}
"""
                with st.spinner("Getting AI Insights & Questions..."):
                    try:
                        response = openai.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are an expert Deloitte subsidy consultant."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        ai_response = response.choices[0].message.content
                        st.markdown("### AI Insights & Recommendations")
                        st.markdown(ai_response)
                    except OpenAIError as e:
                        st.error(f"OpenAI Error: {str(e)}")

        if uploaded_files:
            st.subheader("Ask Questions About the Document")
            followup_question = st.text_input("Type your question about the uploaded document here:")
            if st.button("Ask AI About Document"):
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

    # --- Reset Button ---
    if st.session_state.chat_history:
        if st.button("🔁 Reset Chat"):
            st.session_state.chat_history = []
            st.success("Chat history cleared.")
            st.experimental_rerun()

    # --- Chat History ---
    if st.session_state.chat_history:
        st.markdown("---")
        st.subheader("Conversation History")
        for chat in reversed(st.session_state.chat_history):
            with st.container():
                st.markdown(f"**🧑 You ({chat['timestamp']}):** {chat['question']}")
                st.markdown(f"**🤖 DeloitteSmart™:** {chat['answer']}")
                st.markdown("---")

# --- RIGHT PANEL ---
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
