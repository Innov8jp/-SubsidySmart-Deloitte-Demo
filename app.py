import streamlit as st
import openai

# --- CONFIG ---
st.set_page_config(
    page_title="SubsidySmart™ - Deloitte AI Assistant",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SIDEBAR ---
with st.sidebar:
    st.image("deloitte_logo.png", width=200)
    st.title("SubsidySmart™ Settings")
    openai_api_key = st.text_input("🔑 Enter OpenAI API Key", type="password")
    st.markdown("---")
    st.markdown("Powered by [Innov8]")
    st.markdown("Prototype Version 1.0")
    st.markdown("Secure | Scalable | Smart")

# --- MAIN PAGE ---
st.title("SubsidySmart™: Deloitte Subsidy AI Assistant")
st.caption("Ask any business subsidy question and get instant expert advice, powered by Deloitte AI Agent and real government programs.")

col1, col2 = st.columns([3, 1])

with col1:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.subheader("💬 Ask Your Question")
    user_question = st.text_input("Type your subsidy-related question here:", key="input")

    if st.button("🚀 Ask Deloitte Ai Agent™"):
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

            try:
                with st.spinner("SubsidySmart™ is analyzing your question..."):
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",

                        messages=[
                            {"role": "system", "content": "You are a professional and helpful government subsidy advisor."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    reply = response['choices'][0]['message']['content']
                    st.session_state.chat_history.append({"question": user_question, "answer": reply})
                    st.success("✅ Answer generated below!")

            except Exception as e:
                st.error(f"An error occurred: {e}")

    if st.session_state.chat_history:
        st.markdown("---")
        st.subheader("📜 Conversation History")
        for chat in reversed(st.session_state.chat_history):
            with st.container():
                st.markdown(f"**🧑 You:** {chat['question']}")
                st.markdown(f"**🤖 SubsidySmart™:** {chat['answer']}")
                st.markdown("---")

with col2:
    st.subheader("ℹ️ Information")
    st.markdown("""
    - ✅ SME, R&D, Export Programs  
    - ✅ Real government program documents  
    - ✅ Scalable to full production  
    - ✅ Secure and modular
    """)
    st.subheader("📈 Roadmap")
    st.markdown("""
    - Phase 1: Consultant Use (Today)  
    - Phase 2: Client Portal  
    - Phase 3: Auto Application Drafts  
    - Phase 4: CRM Integration
    """)

