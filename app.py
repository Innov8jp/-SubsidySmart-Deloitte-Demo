# DeloitteSmart™ AI Assistant (Updated with PDF & Multi-Question Support + Language Toggle)

import streamlit as st
import openai
import fitz  # PyMuPDF
import io
import json
from datetime import datetime
from openai import OpenAIError
import os

# --- CONFIG ---
st.set_page_config(
    page_title="DeloitteSmart™ - AI Assistant",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LANGUAGE TOGGLE ---
language = st.sidebar.radio("🌐 Language / 言語", ["English", "日本語"], index=0)

# --- SIDEBAR ---
with st.sidebar:
    st.image("deloitte_logo.png", width=200)
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    st.markdown("✅ OpenAI API key is pre-configured.")
    st.markdown("Powered by [Innov8]")
    st.markdown("Prototype Version 1.0")
    st.markdown("Secure | Scalable | Smart")
    with st.expander("📊 Feedback Analytics"):
        if os.path.exists("feedback_log.json"):
            with open("feedback_log.json", "r", encoding="utf-8") as f:
                feedback_data = [json.loads(line) for line in f.readlines()]

            total_feedback = len(feedback_data)
            helpful_count = sum(1 for f in feedback_data if f["helpful"])
            not_helpful_count = total_feedback - helpful_count

            st.metric("Total Feedback", total_feedback)
            st.metric("👍 Helpful", helpful_count)
            st.metric("👎 Not Helpful", not_helpful_count)
            st.progress(helpful_count / total_feedback if total_feedback else 0)
        else:
            st.info("No feedback data available yet.")

# --- SESSION STATE SETUP ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "user_question" not in st.session_state:
    st.session_state.user_question = ""
if "feedback" not in st.session_state:
    st.session_state.feedback = []
if "show_feedback" not in st.session_state:
    st.session_state.show_feedback = False
if "enable_camera" not in st.session_state:
    st.session_state.enable_camera = False
if "document_content" not in st.session_state:
    st.session_state.document_content = ""

# --- MAIN PAGE ---

# --- FILE UPLOAD AND DOCUMENT PARSING ---
upload_label = "Upload Documents (PDF, TXT)" if language == "English" else "資料をアップロード (PDF, TXT)"
with st.expander(upload_label):
    uploaded_files = st.file_uploader("", type=["pdf", "txt"], accept_multiple_files=True)

    if uploaded_files:
        doc_text = ""
        st.markdown("### Uploaded Files:")
        for file in uploaded_files:
            st.markdown(f"- `{file.name}`")  # Show file name
            file_bytes = file.read()
            if file.type == "application/pdf":
                try:
                    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                        for page in doc:
                            doc_text += page.get_text()
                except Exception as e:
                    st.error(f"PDF extraction error: {str(e)}")
            elif file.type == "text/plain":
                doc_text += file_bytes.decode("utf-8")
        st.session_state.document_content = doc_text

        # Show document preview
        preview_label = "**Extracted Text Preview:**" if language == "English" else "**抽出されたテキストのプレビュー：**"
        st.markdown(preview_label)
        st.code(st.session_state.document_content[:2000], language="markdown")
    else:
        st.session_state.document_content = ""

title_text = "DeloitteSmart™: Your AI Assistant for Faster, Smarter Decisions" if language == "English" else "DeloitteSmart™：より速く、よりスマートな意思決定を支援するAIアシスタント"
caption1 = "Ask any business domain specific question and get instant expert advice, powered by Deloitte AI Agent." if language == "English" else "業務に関する質問を入力すると、DeloitteのAIエージェントが即座に専門的なアドバイスを提供します。"
caption2 = "より速く、よりスマートな意思決定のためのAIアシスタント"  # Always show JP subtitle

st.title(title_text)
st.caption(caption2)
st.caption(caption1)

mode_label = "Choose interaction mode:" if language == "English" else "モードを選択してください："
mode = st.radio(mode_label, ["Client-Asks (Default)", "Deloitte-Asks"], index=0)
col1, col2 = st.columns([3, 1])

# --- LEFT COLUMN ---
with col1:
    if mode == "Client-Asks (Default)":
        st.subheader("Ask Your Question" if language == "English" else "質問を入力")
        st.text_input("Type your subsidy-related question here:" if language == "English" else "補助金に関する質問を入力してください：", key="user_question")

        ask_btn_label = "Ask Deloitte AI Agent™" if language == "English" else "Deloitte AIエージェントに質問する"
        if st.button(ask_btn_label):
            user_question = st.session_state.user_question.strip()

            if not openai_api_key:
                st.error("API key missing." if language == "English" else "APIキーが設定されていません。")
            elif not user_question:
                st.warning("Please enter a question." if language == "English" else "質問を入力してください。")
            else:
                openai.api_key = openai_api_key
                context = st.session_state.get("document_content", "No document uploaded." if language == "English" else "資料がアップロードされていません。")
                prompt = f"""
You are a highly experienced Deloitte consultant specializing in Japanese government subsidies.

Use the following context (if any) and the user's question to respond precisely:

Context Document:
{context}

User Question: {user_question}
"""
                with st.spinner("Analyzing with DeloitteSmart™..." if language == "English" else "DeloitteSmart™で分析中..."):
                    try:
                        response = openai.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are a highly experienced Deloitte consultant specializing in Japanese government subsidies."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        reply = response.choices[0].message.content
                        entry = {
                            "question": user_question,
                            "answer": reply,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        st.session_state.chat_history.append(entry)
                        st.session_state.show_feedback = True

                        with open("chat_feedback_log.json", "a", encoding="utf-8") as f:
                            f.write(json.dumps(entry) + "\n")

                        st.success("✅ Answer generated below!" if language == "English" else "✅ 回答が生成されました：")
                        st.markdown(reply)

                    except OpenAIError as e:
                        st.error(f"OpenAI API Error: {str(e)}")

# --- DELOITTE ASKS ---
    elif mode == "Deloitte-Asks":
        st.subheader("Get Smart Questions to Ask Your Client" if language == "English" else "クライアントに尋ねるべきスマートな質問")
        client_profile = st.text_area("Describe the client (industry, size, goal, etc.):" if language == "English" else "クライアントの情報を記述してください（業種、規模、目標など）：", key="client_profile")

        st.session_state.enable_camera = st.toggle("📷 Enable Camera Input" if language == "English" else "📷 カメラ入力を有効にする", key="enable_camera_toggle")
        captured_image = st.camera_input("Take a picture" if language == "English" else "写真を撮る", key="camera") if st.session_state.enable_camera else None

        insights_btn_label = "Get AI Insights & Questions" if language == "English" else "AIによる分析と質問を取得"
        if st.button(insights_btn_label):
            if not openai_api_key:
                st.error("API key missing." if language == "English" else "APIキーが設定されていません。")
            elif not client_profile.strip():
                st.warning("Please describe the client first." if language == "English" else "まずクライアント情報を記述してください。")
            else:
                openai.api_key = openai_api_key
                prompt = f"""
You are SubsidySmart™, a Deloitte AI assistant. Analyze the following:

1. Client Profile
2. Uploaded Documents
3. Recommend 1-2 relevant subsidy programs.
4. Ask 2-3 insightful follow-up questions.

Client Profile:
{client_profile}

Client Document:
{st.session_state.document_content}
"""
                with st.spinner("Getting AI Insights & Questions..." if language == "English" else "AIによる分析と質問を取得中..."):
                    try:
                        response = openai.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are a Deloitte subsidy expert."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        ai_response = response.choices[0].message.content
                        st.markdown("### AI Insights & Recommendations" if language == "English" else "### AIによる分析と推奨")
                        st.markdown(ai_response)
                    except OpenAIError as e:
                        st.error(f"OpenAI API Error: {str(e)}")

# --- (rest of the Deloitte-Asks logic and UI elements remain unchanged) ---
# (If needed, this section can also be localized similarly)
