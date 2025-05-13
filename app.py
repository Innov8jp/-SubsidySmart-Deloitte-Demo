# DeloitteSmart™ AI Assistant – Full Version (Enhanced Multi-Doc Summarizer, Persistent Chat, Feedback, Downloadable Report - Basic Chunking)

import streamlit as st
import openai
import fitz  # PyMuPDF
import json
from datetime import datetime
from openai import OpenAIError
import os
from io import BytesIO
import base64
import re  # Import regular expressions for splitting
import time # Import time (used implicitly by spinners/status)

# --- CONFIGURATION - MUST BE FIRST ---
# Set page configuration for the Streamlit app
st.set_page_config(
    page_title="DeloitteSmart™ - AI Assistant",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONSTANTS ---
# Maximum approximate characters to include in the chat prompt context from documents
# This is a heuristic based on token limits (~4 chars per token for English).
# GPT-3.5-turbo often has a 16k token limit, leaving room for prompt/response.
MAX_CONTEXT_CHARS = 14000
# Smaller chunk size used *before* joining into MAX_CONTEXT_CHARS.
# This size is used for the individual chunks stored and processed.
SPLIT_CHUNK_SIZE = 1500 # Slightly larger chunk size for better context within chunks

# --- LANGUAGE TOGGLE AND TRANSLATION FUNCTION ---
# Allow users to select language via a radio button in the sidebar
language = st.sidebar.radio("🌐 Language / 言語", ["English", "日本語"], index=0, key="language_select")

# Dictionary containing English to Japanese translations
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
        "Error during document processing for": "のドキュメント処理エラー:",
        "You are a highly trained consultant. Summarize the following content and generate 5 smart questions to ask the client.": "あなたは高度な訓練を受けたコンサルタントです。以下の内容を要約し、クライアントに尋ねるべき5つのスマートな質問を生成してください。",
        "Document:": "ドキュメント:",
        "Documents:": "ドキュメント:", # Used for chat prompt context
        "Question:": "質問:",
        "# DeloitteSmart™ AI Assistant Report\n\n## Document Summaries:\n": "# DeloitteSmart™ AIアシスタントレポート\n\n## ドキュメントの要約:\n",
        "## Chat History:\n": "## チャット履歴:\n",
        "Download Report": "レポートをダウンロード",
        "Send": "送信",
        "Please upload documents before asking questions.": "質問する前にドキュメントをアップロードしてください。",
        "OpenAI API key is not available. Cannot generate summary.": "OpenAI APIキーが利用できません。要約を生成できません。",
        "OpenAI API key is not available. Cannot answer questions.": "OpenAI APIキーが利用できません。質問に答えることができません。",
        "Processing document": "ドキュメントを処理中",
        "Extracting text from": "からテキストを抽出中:",
        "Splitting into chunks:": "に分割中:",
        "Generating summary and questions for": "の要約と質問を生成中:",
        "OpenAI API key is pre-configured.": "OpenAI APIキーは事前に構成されています。",
        "OpenAI API key not found.": "OpenAI APIキーが見つかりません。",
        "Powered by [Innov8]": "[Innov8] 提供",
        "Prototype Version 1.0": "プロトタイプ バージョン 1.0",
        "Secure | Scalable | Smart": "安全 | スケーラブル | スマート",
        "Note: This document is large and analysis uses chunks, which may impact summary/answer accuracy.": "注: このドキュメントはサイズが大きいため、分析にはチャンクが使用され、要約や回答の精度に影響する可能性があります。",
        "Generating response...": "応答を生成中...",
        "Sending query to AI...": "AIにクエリを送信中...",
        "Response received!": "応答を受信しました！",
        "Error!": "エラー！",
        "No document content available or chunks are too large to fit in context.": "利用可能なドキュメント コンテンツがないか、またはチャンクが大きすぎてコンテキストに収まりません。",
        "No text extracted from": "からテキストが抽出されませんでした:",
        "Summary generation skipped (API key missing).": "要約生成はスキップされました (APIキーがありません)。",
        "Error during document processing for": "のドキュメント処理エラー:",
        "Text extraction failed": "テキスト抽出に失敗しました",
        "Chunking failed": "チャンク化に失敗しました",
        "Summary generation error for": "の要約生成エラー:",

    }
    return translations.get(english_text, english_text) if language == "日本語" else english_text

# --- HELPER FUNCTIONS ---

# Basic text splitting function to handle large documents
def split_text_into_chunks(text, chunk_size=SPLIT_CHUNK_SIZE):
    """Splits text by paragraphs, then joins into chunks of approximate size."""
    if not text:
        return []

    # Split by multiple newlines (paragraphs)
    paragraphs = re.split(r'\n\s*\n', text)

    chunks = []
    current_chunk = ""
    for para in paragraphs:
        # If adding the next paragraph makes the current chunk too large
        # (add +2 for the potential "\n\n" that will join them later)
        if len(current_chunk) + len(para) + 2 > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = para.strip() # Start new chunk with this paragraph
        else:
            if current_chunk:
                current_chunk += "\n\n" + para.strip()
            else:
                current_chunk = para.strip()

    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)

    # Secondary split for any chunks that are still too large (e.g., single massive paragraphs)
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > chunk_size:
            # Simple character split as a fallback
            sub_chunks = [chunk[i:i+chunk_size] for i in range(0, len(chunk), chunk_size)]
            final_chunks.extend(sub_chunks)
        else:
            final_chunks.append(chunk)

    # Remove any empty strings resulting from splits
    return [c for c in final_chunks if c]

# --- SIDEBAR ---
# Set up the sidebar with logo, API key status, and branding
with st.sidebar:
    st.image("deloitte_logo.png", width=200) # Assuming deloitte_logo.png is in the same directory
    openai_api_key = st.secrets.get("OPENAI_API_KEY")
    if openai_api_key:
        st.sidebar.success(get_translation("OpenAI API key is pre-configured."))
    else:
        st.sidebar.error(get_translation("OpenAI API key not found."))
    st.sidebar.markdown(get_translation("Powered by [Innov8]"))
    st.sidebar.markdown(get_translation("Prototype Version 1
