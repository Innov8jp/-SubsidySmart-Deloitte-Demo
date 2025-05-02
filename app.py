import streamlit as st
import openai
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

# --- APP CONFIGURATION ---
PAGE_TITLE = "DeloitteSmart™ Consultant Portal"
PAGE_ICON = ":briefcase:"
LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "expanded"
DELOITTE_LOGO = "deloitte_logo.png"

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state=INITIAL_SIDEBAR_STATE
)

# --- AUTHENTICATION ---
internal_password = st.secrets.get("INTERNAL_PASS", "")
access_code = st.text_input("Enter internal access code:", type="password")
if access_code != internal_password:
    st.error("Unauthorized. Please contact your admin.")
    st.stop()

# --- SECRETS & GOOGLE SHEETS SETUP ---
openai_api_key = st.secrets["OPENAI_API_KEY"]
gsheet_credentials = st.secrets["GSHEET_CREDENTIALS"]
gsheet_id = st.secrets["GSHEET_ID"]

creds = Credentials.from_service_account_info(
    gsheet_credentials,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
gc = gspread.Client(auth=creds)
sheet = gc.open_by_key(gsheet_id).sheet1

data = pd.DataFrame(sheet.get_all_records())

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists(DELOITTE_LOGO):
        st.image(DELOITTE_LOGO, width=150)
    st.markdown(f"### {PAGE_TITLE}")
    st.markdown("Secure | Scalable | Smart")
    st.markdown(f"Total Submissions: **{len(data)}**")
    st.markdown("---")

# --- MAIN ---
st.title("Consultant Dashboard")
st.subheader("Client Registrations & Scores")
st.dataframe(data)

st.subheader("Generate Interview Questions")
client_profile = st.text_area("Paste client profile (industry, size, goals):")
if st.button("Generate Questions") and client_profile:
    prompt = (
        "You are SubsidySmart™, a Deloitte-trained AI consultant. "
        "Based on this client profile, generate a concise list of key assessment questions.\n"
        + client_profile
    )
    with st.spinner("Generating questions..."):
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional Deloitte consultant."},
                {"role": "user", "content": prompt}
            ]
        )
    st.markdown("### Suggested Questions to Ask Client")
    st.markdown(response.choices[0].message.content)

st.subheader("Roadmap & Next Steps")
st.markdown(
    "- Pilot with 5 consultants and 10 clients\n"
    "- Integrate with CRM (Salesforce)\n"
    "- Scale to full production by Q3"
)
