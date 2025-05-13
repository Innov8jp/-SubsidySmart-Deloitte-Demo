# DeloitteSmart™ AI Assistant – Full Version (Enhanced Multi-Doc Summarizer, Persistent Chat, Downloadable Report, Feedback)

import streamlit as st
import openai
import fitz  # PyMuPDF
import json
from datetime import datetime
from openai import OpenAIError
import os
from io import BytesIO
import base64

# --- CONFIGURATION - MUST BE FIRST ---
st.set_page_config(
    page_title="DeloitteSmart™ - AI Assistant",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LANGUAGE TOGGLE ---
language = st.sidebar.radio("🌐 Language / 言語", ["English", "日本語"], index=0)

def get_translation(english_text):
    translations = {
        "DeloitteSmart™ - AI Assistant": "DeloitteSmart™ - AIアシスタント",
        "Faster, Smarter Decisions": "より速く、よりスマートな意思決定",
        "📁 Upload Documents (PDF, TXT)": "📁 ドキュメントをアップロード (PDF, TXT)",
        "📄 Summaries & Smart Questions": "📄 要約とスマートな質問",
        "🗂️": "🗂️",
        "---": "---",
        "🗣️ Ask Questions Based on the Documents": "🗣️ ドキュメントに基づいて質問する",
        "Ask anything about the uploaded documents...": "アップロードしたドキュメントについて何でも質問してください...",
        "💬 Chat History": "💬 チャット履歴",
        "User": "ユーザー",
        "Assistant": "アシスタント",
        "⬇️ Download Report": "⬇️ レポートをダウンロード",
        "📝 Feedback": "📝 フィードバック",
        "Share your feedback to help us improve:": "改善のため、フィードバックをお聞かせください:",
        "Submit Feedback": "フィードバックを送信",
        "Thank you for your feedback!": "ご意見ありがとうございます！",
        "Please enter your feedback.": "フィードバックを入力してください。",
        "📬 Submitted Feedback": "📬 送信されたフィードバック",
        "Timestamp": "タイムスタンプ",
        "PDF extraction error for": "のPDF抽出エラー:",
        "Summary generation error for": "の要約生成エラー:",
        "Error during chat completion:": "チャット完了中にエラーが発生しました:",
        "You are a highly trained consultant. Summarize the following content and generate 5 smart questions to ask the client.": "あなたは高度な訓練を受けたコンサルタントです。以下の内容を要約し、クライアントに尋ねるべき5つのスマートな質問を生成してください。",
        "Document:": "ドキュメント:",
        "You are an AI assistant specialized in summarizing and extracting smart questions.": "あなたは、要約とスマートな質問の抽出に特化したAIアシスタントです。",
        "You are a helpful AI assistant designed to answer questions based on the provided documents.\nAnalyze the following documents and answer the user's question as accurately and concisely as possible.\nIf the answer is not explicitly found in the documents, state that you cannot find the answer.": "あなたは、提供されたドキュメントに基づいて質問に答えるように設計された、役立つAIアシスタントです。\n以下のドキュメントを分析し、ユーザーの質問に可能な限り正確かつ簡潔に答えてください。\n答えがドキュメントに明示的に見つからない場合は、答えが見つからないと述べてください。",
        "Question:": "質問:",
        "# DeloitteSmart™ AI Assistant Report\n\n## Document Summaries:\n": "# DeloitteSmart™ AIアシスタントレポート\n\n## ドキュメントの要約:\n",
        "## Chat History:\n": "## チャット履歴:\n",
        "Download Report": "レポートをダウンロード",
        "Send": "送信",
        "Please upload documents before asking questions.": "質問する前にドキュメントをアップロードしてください。",
        "OpenAI API key is not available. Cannot generate summary.": "OpenAI APIキーが利用できません。要約を生成できません。",
        "OpenAI API key is not available. Cannot answer questions.": "OpenAI APIキーが利用できません。質問に答えることができません。",
    }
    return translations.get(english_text, english_text) if language == "日本語" else english_text

# --- SIDEBAR ---
with st.sidebar:
    st.image("deloitte_logo.png", width=200)
    openai_api_key = st.secrets.get("OPENAI_API_KEY")
    if openai_api_key:
        st.markdown(get_translation("✅ OpenAI API key is pre-configured."))
    else:
        st.error(f"⚠️ {get_translation('OpenAI API key not found in secrets.')}")
    st.markdown(get_translation("Powered by [Innov8]"))
    st.markdown(get_translation("Prototype Version 1.0"))
    st.markdown(get_translation("Secure | Scalable | Smart"))

# --- SESSION STATE SETUP ---
session_defaults = {
    "chat_history": [],
    "user_question": "",
    "feedback": [],
    "show_feedback": False,
    "document_content": {},
    "document_summary": {},
    "uploaded_filenames": []
}
for key, default in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- MAIN PAGE ---
title_text = get_translation("DeloitteSmart™: Your AI Assistant for Faster, Smarter Decisions")
st.title(title_text)

# --- FILE UPLOAD ---
with st.expander(get_translation("📁 Upload Documents (PDF, TXT)")):
    uploaded_files = st.file_uploader("", type=["pdf", "txt"], accept_multiple_files=True)
    if uploaded_files:
        for file in uploaded_files:
            filename = file.name
            if filename not in st.session_state.uploaded_filenames:
                st.session_state.uploaded_filenames.append(filename)
                st.session_state.document_content[filename] = ""
                st.session_state.document_summary[filename] = ""
                file_bytes = file.read()
                try:
                    if file.type == "application/pdf":
                        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                            for page in doc:
                                st.session_state.document_content[filename] += page.get_text()
                    elif file.type == "text/plain":
                        st.session_state.document_content[filename] = file_bytes.decode("utf-8")

                    # Summarize
                    if openai_api_key:
                        prompt = f"""{get_translation("You are a highly trained consultant. Summarize the following content and generate 5 smart questions to ask the client.")}

{get_translation("Document:")}
{st.session_state.document_content[filename]}
"""
                        try:
                            client = openai.OpenAI(api_key=openai_api_key)
                            response = client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[
                                    {"role": "system", "content": get_translation("You are an AI assistant specialized in summarizing and extracting smart questions.")},
                                    {"role": "user", "content": prompt}
                                ]
                            )
                            st.session_state.document_summary[filename] = response.choices[0].message.content
                        except OpenAIError as e:
                            st.error(f"{get_translation('Summary generation error for')} {filename}: {str(e)}")
                    else:
                        st.warning(get_translation("OpenAI API key is not available. Cannot generate summary."))
                except Exception as e:
                    st.error(f"{get_translation('PDF extraction error for')} {filename}: {str(e)}")

# --- SHOW SUMMARIES ---
if st.session_state.document_summary:
    st.subheader(get_translation("📄 Summaries & Smart Questions"))
    for fname, summary in st.session_state.document_summary.items():
        st.markdown(f"#### {get_translation('🗂️')} {fname}")
        escaped_summary =
