import streamlit as st
import openai
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="DeloitteSmart™ Consultant Portal",
    page_icon=":briefcase:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- AUTHENTICATION ---
access_code = st.text_input("Enter internal access code:", type="password")
if access_code != st.secrets.get("INTERNAL_PASS", ""):
    st.error("Unauthorized. Please contact your admin.")
    st.stop()

# --- SECRETS & GOOGLE SHEETS SETUP ---
openai.api_key = st.secrets["OPENAI_API_KEY"]
creds = Credentials.from_service_account_info(
    st.secrets["GSHEET_CREDENTIALS"],
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
gc    = gspread.Client(auth=creds)
sheet = gc.open_by_key(st.secrets["GSHEET_ID"]).sheet1

data = pd.DataFrame(sheet.get_all_records())

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("deloitte_logo.png"):
        st.image("deloitte_logo.png", width=150)
    st.markdown("### DeloitteSmart™ Consultant Portal")
    st.markdown("Secure | Scalable | Smart")
    st.markdown(f"Total Submissions: **{len(data)}**")
    st.markdown("---")

# --- MAIN ---
st.title("Consultant Dashboard")
st.subheader("Client Registrations & Scores")
st.dataframe(data)

st.subheader("Generate Interview Questions")
profile = st.text_area("Paste client profile (industry, size, goals):")
if st.button("Generate Questions") and profile:
    prompt = (
        "You are SubsidySmart™, a Deloitte-trained AI consultant. "
        "Based on this client profile, generate a concise list of key assessment questions.\n"
        + profile
    )
    with st.spinner("Generating questions..."):
        resp = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role":"system","content":"You are a professional Deloitte consultant."},
                {"role":"user","content":prompt}
            ]
        )
    st.markdown("### Suggested Questions to Ask Client")
    st.markdown(resp['choices'][0]['message']['content'])

st.subheader("Roadmap & Next Steps")
st.markdown(
    "- Pilot with 5 consultants and 10 clients\n"
    "- Integrate with CRM (Salesforce)\n"
    "- Scale to full production by Q3"
)
