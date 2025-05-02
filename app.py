# app.py – DeloitteSmart™ Client Portal
# Email and Google Sheet functionality are optional and controlled by toggles

import streamlit as st
import openai
from datetime import datetime
from fpdf import FPDF
import os
import csv

# Uncomment these imports when enabling features
# import yagmail
# import gspread
# from google.oauth2.service_account import Credentials

# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="DeloitteSmart™ Client Portal",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FEATURE TOGGLES ---
ENABLE_EMAIL = False   # Set True to enable email sending
ENABLE_GSHEET = False  # Set True to enable Google Sheets logging

# --- HELPER: Clean text for PDF ---
def safe_text(txt: str) -> str:
    replacements = {'™':'(TM)','–':'-','≥':'>=','✓':'v','✔':'v'}
    for k, v in replacements.items():
        txt = txt.replace(k, v)
    return txt.encode('latin1', 'ignore').decode('latin1')

# --- SECRETS & OPTIONAL SETUP ---
openai.api_key = st.secrets.get("OPENAI_API_KEY", "")
\if ENABLE_EMAIL:
    email_user = st.secrets.get("EMAIL_USER", "")
    email_pass = st.secrets.get("EMAIL_PASS", "")

if ENABLE_GSHEET:
    creds_info = st.secrets.get("GSHEET_CREDENTIALS", {})
    creds = Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    gc = gspread.Client(auth=creds)
    sheet = gc.open_by_key(st.secrets.get("GSHEET_ID", "")).sheet1

    # Ensure header row exists
    if not sheet.get_all_records():
        sheet.append_row([
            "timestamp","name","email","company",
            "score","status","report_recipient","internal_cc"
        ])

# --- REGISTRATION FLOW ---
if "registered" not in st.session_state:
    st.session_state.registered = False

if not st.session_state.registered:
    st.title("Welcome to DeloitteSmart™ Client Portal")
    st.subheader("Please register to continue")
    name = st.text_input("Your Name")
    mail = st.text_input("Your Email")
    comp = st.text_input("Company Name")
    if st.button("Register"):
        if not (name and mail and comp):
            st.error("All fields are required.")
        else:
            ts = datetime.now().isoformat()
            # Save to local CSV
            fpath = "registrations.csv"
            new_file = not os.path.exists(fpath)
            with open(fpath, "a", newline="") as f:
                w = csv.writer(f)
                if new_file:
                    w.writerow(["timestamp","name","email","company"] )
                w.writerow([ts, name, mail, comp])
            # Optional: log to Google Sheet
            if ENABLE_GSHEET:
                sheet.append_row([ts, name, mail, comp])
            # Update session
            st.session_state.registered = True
            st.session_state.user_name    = name
            st.session_state.user_email   = mail
            st.session_state.company      = comp
            st.success(f"Registered as {name} ({comp})!")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("deloitte_logo.png"):
        st.image("deloitte_logo.png", width=200)
    st.markdown(f"### User: {st.session_state.user_name}")
    st.markdown(f"#### Company: {st.session_state.company}")
    st.markdown("---")
    st.markdown("Secure | Intelligent | Personalized")

# --- MAIN LAYOUT ---
st.title(f"Hello {st.session_state.user_name}, welcome back!")
mode = st.radio("Mode:", ["Chat with AI", "Eligibility Self-Check"], index=0)

# --- CHAT WITH AI ---
if mode == "Chat with AI":
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    st.subheader("Ask a question about government subsidies")
    q = st.text_input("Your question:")
    if st.button("Send") and q:
        prompt = f"You are SubsidySmart(TM), an expert subsidy advisor. Question: {q}"
        with st.spinner("AI is responding..."):
            resp = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role":"system","content":"You are a professional subsidy advisor."},
                    {"role":"user","content":prompt}
                ]
            )
            a = resp['choices'][0]['message']['content']
        st.session_state.chat_history.append((q, a))
    for qq, aa in reversed(st.session_state.chat_history):
        st.markdown(f"**You:** {qq}")
        st.markdown(f"**AI:** {aa}")
        st.markdown("---")

# --- ELIGIBILITY SELF-CHECK & REPORT ---
else:
    st.subheader("Eligibility Self-Check & Report")
    recipient = st.text_input("Send report to Email:", value=st.session_state.user_email)
    age       = st.radio("Company age?", ["<3 years","≥3 years"])
    industry  = st.multiselect("Industry(s)",["AI","IoT","Biotech","Green Energy","Other"])
    rd        = st.radio("R&D Budget?", ["<200K","≥200K"])
    exp       = st.radio("Export?", ["No","Yes"])
    rev       = st.radio("Revenue?", ["<500K","≥500K"])
    emp       = st.slider("Employees", 1, 200, 10)
    docs      = st.multiselect("Documents Provided",["Business Plan","Org Chart","Budget","Export Plan","Pitch Deck"])

    if st.button("Calculate & Send Report"):
        # Calculate score
        score = 0
        score += 15 if age == "≥3 years" else 0
        score += 20 if any(i in industry for i in ["AI","IoT","Biotech","Green Energy"]) else 0
        score += 20 if rd == "≥200K" else 0
        score += 15 if exp == "Yes" else 0
        score += 10 if rev == "≥500K" else 0
        score += 10 if 5 <= emp <= 100 else 0
        score += len(docs) * 2
        status = "Highly Eligible" if score >= 85 else ("Needs Review" if score >= 65 else "Not Eligible")

        st.metric("Eligibility Score", f"{score}%")
        st.markdown(f"**{status}**")

        # Optional: log to Google Sheet
        if ENABLE_GSHEET:
            row = [
                datetime.now().isoformat(),
                st.session_state.user_name,
                st.session_state.user_email,
                st.session_state.company
            ]
            sheet.append_row(row)

        # Generate PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, safe_text("DeloitteSmart(TM) Subsidy Report"), ln=1, align='C')
        pdf.ln(5)
        info = f"User: {st.session_state.user_name} | Score: {score}% - {status}"
        pdf.multi_cell(0, 8, safe_text(info))
        pdf.ln(5)
        details = [
            f"Age: {age}",
            f"Industry: {', '.join(industry)}",
            f"R&D: {rd}",
            f"Export: {exp}",
            f"Revenue: {rev}",
            f"Employees: {emp}",
            f"Docs: {', '.join(docs)}"
        ]
        pdf.multi_cell(0, 8, safe_text("\n".join(details)))
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        fn = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        st.download_button("Download PDF Report", data=pdf_bytes, file_name=fn, mime='application/pdf')

        # Optional: send email
        if ENABLE_EMAIL and email_user and email_pass and recipient:
            yag = yagmail.SMTP(email_user, email_pass)
            yag.send(
                to=[recipient, "asif.baig@innov8.jp"],
                subject="Your DeloitteSmart(TM) Subsidy Report",
                contents=safe_text("Please see attached report."),
                attachments={fn: pdf_bytes}
            )
            st.success("Emailed to client and Innov8.")
