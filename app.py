import streamlit as st
import openai
from datetime import datetime

# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="DeloitteSmart™ Consultant Portal",
    page_icon=":briefcase:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- OPENAI SETUP ---
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- MAIN INTERFACE ---
st.title("DeloitteSmart™: Your AI Assistant")
mode = st.radio("Mode:", ["Client-Asks", "Deloitte-Asks"], index=0)

# Client-Asks flow
if mode == "Client-Asks":
    if "history" not in st.session_state:
        st.session_state.history = []
    st.subheader("Client Questions")
    q = st.text_input("Question from client:")
    if st.button("Ask AI") and q:
        prompt = f"You are a professional subsidy advisor. Question: {q}"
        with st.spinner("AI is responding..."):
            resp = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role":"system","content":"You are a helpful subsidy advisor."},
                    {"role":"user","content":prompt}
                ]
            )
        a = resp.choices[0].message.content
        st.session_state.history.append((q, a))
    for cq, ca in reversed(st.session_state.history):
        st.markdown(f"**Client:** {cq}")
        st.markdown(f"**AI:** {ca}")
        st.markdown("---")

# Deloitte-Asks flow w/ scoring
else:
    st.subheader("Get Questions to Ask Your Client")
    profile = st.text_area("Client profile (industry, size, goals):")

    with st.expander("📝 Optional: Score this client"):
        age         = st.radio("Company age?", ["<3 years","≥3 years"])
        industry    = st.multiselect("Industry?", ["AI","IoT","Biotech","Green Energy","Other"])
        rd_budget   = st.radio("R&D Budget?", ["<200K","≥200K"])
        exp_ready   = st.radio("Exporting?", ["No","Yes"])
        revenue     = st.radio("Annual Revenue?", ["<500K","≥500K"])
        employees   = st.slider("Employees", 1, 200, 10)
        documents   = st.multiselect("Documents provided", ["Business Plan","Org Chart","Budget","Export Plan","Pitch Deck"])

    if st.button("Generate Consultant Questions") and profile:
        # AI Q-list
        prompt = (
            "You are a professional Deloitte consultant. "
            "Based on this client profile, generate key assessment questions:\n" + profile
        )
        with st.spinner("Generating questions..."):
            resp = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role":"system","content":"You are a skilled consultant."},
                    {"role":"user","content":prompt}
                ]
            )
        st.markdown("### Suggested Questions")
        st.markdown(resp.choices[0].message.content)

        # Eligibility scoring
        score = 0
        if age == "≥3 years":                   score += 15
        if any(i in industry for i in ["AI","IoT","Biotech","Green Energy"]): score += 20
        if rd_budget == "≥200K":                score += 20
        if exp_ready == "Yes":                  score += 15
        if revenue == "≥500K":                  score += 10
        if 5 <= employees <= 100:              score += 10
        score += len(documents) * 2

        st.markdown("### 🧮 Eligibility Score")
        st.metric("Score (%)", f"{score}%")
        if score >= 85:
            st.success("🟢 Highly Eligible")
        elif score >= 65:
            st.warning("🟡 Potentially Eligible — Requires Review")
        else:
            st.error("🔴 Low Eligibility or Incomplete")
