# DeloitteSmart™ AI Assistant – Full Version (Enhanced Multi-Doc Summarizer, Persistent Chat, Feedback, Downloadable Report - Basic Chunking)

import streamlit as st
import openai
import fitz  # PyMuPDF
import json
from datetime import datetime
from openai import OpenAIError
import os
from io import BytesIO
import base64
import re # Import regular expressions for splitting

# --- CONFIGURATION - MUST BE FIRST ---
# Set page configuration for the Streamlit app
st.set_page_config(
    page_title="DeloitteSmart™ - AI Assistant",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONSTANTS ---
# Maximum approximate characters per chunk for splitting large documents
# This is a heuristic; actual token count is model-dependent (1 token ~ 4 chars for English)
# GPT-3.5-turbo often has a 16k token limit, so ~14000 chars leaves room for prompt/response
MAX_CHUNK_CHARS = 14000
# Smaller chunk size for splitting strategy
SPLIT_CHUNK_SIZE = 1000

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
        "Documents:": "ドキュメント:", # Added for chat prompt context
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
        "Processing document": "ドキュメントを処理中",
        "Generating summary and questions for": "の要約と質問を生成中:",
        "OpenAI API key is pre-configured.": "OpenAI APIキーは事前に構成されています。",
        "OpenAI API key not found.": "OpenAI APIキーが見つかりません。",
        "Powered by [Innov8]": "[Innov8] 提供",
        "Prototype Version 1.0": "プロトタイプ バージョン 1.0",
        "Secure | Scalable | Smart": "安全 | スケーラブル | スマート",
        "This document is large and has been split into chunks for analysis.": "このドキュメントはサイズが大きいため、分析のために分割されました。",
    }
    return translations.get(english_text, english_text) if language == "日本語" else english_text

# --- HELPER FUNCTIONS ---

# Basic text splitting function to handle large documents
def split_text_into_chunks(text, chunk_size=SPLIT_CHUNK_SIZE):
    """Splits text by paragraphs, then joins into chunks of approximate size."""
    if not text:
        return []
    paragraphs = re.split(r'\n\s*\n', text) # Split by two or more newlines (paragraphs)
    chunks = []
    current_chunk = ""
    for para in paragraphs:
        # If adding the next paragraph exceeds the chunk size, save the current chunk
        # and start a new one. Add +2 for potential \n\n between paragraphs.
        if len(current_chunk) + len(para) + 2 > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
    if current_chunk:
        chunks.append(current_chunk.strip())

    # Fallback split by character if paragraphs are too large
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > chunk_size:
            # Simple character split if paragraph is too big
            sub_chunks = [chunk[i:i+chunk_size] for i in range(0, len(chunk), chunk_size)]
            final_chunks.extend(sub_chunks)
        else:
            final_chunks.append(chunk)

    return final_chunks


# --- SIDEBAR ---
# Set up the sidebar with logo, API key status, and branding
with st.sidebar:
    st.image("deloitte_logo.png", width=200) # Assuming deloitte_logo.png is in the same directory
    openai_api_key = st.secrets.get("OPENAI_API_KEY")
    if openai_api_key:
        st.sidebar.success(get_translation("✅ OpenAI API key is pre-configured."))
    else:
        st.sidebar.error(get_translation("❌ OpenAI API key not found."))
    st.sidebar.markdown(get_translation("Powered by [Innov8]"))
    st.sidebar.markdown(get_translation("Prototype Version 1.0"))
    st.sidebar.markdown(get_translation("Secure | Scalable | Smart"))

# --- SESSION STATE SETUP ---
# Initialize session state variables if they don't exist
session_defaults = {
    "chat_history": [],   # Stores the chat conversation
    "user_question": "", # Temporary storage for user input
    "feedback": [],      # Stores submitted feedback
    "document_content": {}, # Stores raw text content of uploaded documents {filename: text}
    "document_chunks": {}, # Stores processed chunks of documents {filename: [chunk1, chunk2, ...]}
    "document_summary": {}, # Stores summaries {filename: summary_text}
    "uploaded_filenames": [] # Tracks names of files already processed in this session
}
for key, default in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- TITLE ---
st.title(get_translation("DeloitteSmart™: Your AI Assistant for Faster, Smarter Decisions"))

# --- FILE UPLOAD ---
# Expander for file upload section
with st.expander(get_translation("📁 Upload Documents (PDF, TXT)")):
    uploaded_files = st.file_uploader(
        get_translation("Upload Files"),
        type=["pdf", "txt"],
        accept_multiple_files=True,
        key="file_uploader" # Added a key
    )

    # Process uploaded files
    if uploaded_files:
        for file in uploaded_files:
            filename = file.name
            # Check if file has already been processed in this session
            if filename not in st.session_state.uploaded_filenames:
                # Add a spinner while processing each file
                with st.spinner(f"{get_translation('Processing document')} {filename}..."):
                    st.session_state.uploaded_filenames.append(filename)
                    file_bytes = file.getvalue() # Use getvalue() for BytesIO like object

                    document_text = ""
                    try:
                        if file.type == "application/pdf":
                            # Use BytesIO to read PDF from bytes
                            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                                for page in doc:
                                    document_text += page.get_text() + "\n" # Add newline between pages
                        elif file.type == "text/plain":
                            document_text = file_bytes.decode("utf-8")

                        st.session_state.document_content[filename] = document_text.strip() # Store full content

                        # Split document into chunks for chat context (especially for large files)
                        st.session_state.document_chunks[filename] = split_text_into_chunks(
                            document_text, chunk_size=SPLIT_CHUNK_SIZE
                        )

                        # Summarize if API key is available
                        if openai_api_key:
                            # Use the full text for summarization if not too large,
                            # otherwise use the first few chunks as context might be lost over chunks
                            summary_text_source = document_text if len(document_text) < MAX_CHUNK_CHARS else " ".join(st.session_state.document_chunks[filename][:5]) # Use first 5 chunks if very large

                            if summary_text_source:
                                try:
                                    with st.spinner(f"{get_translation('Generating summary and questions for')} {filename}..."):
                                        prompt = f"{get_translation('You are a highly trained consultant. Summarize the following content and generate 5 smart questions.')}\n\n{get_translation('Document:')}\n{summary_text_source}"
                                        client = openai.OpenAI(api_key=openai_api_key)
                                        response = client.chat.completions.create(
                                            model="gpt-3.5-turbo", # Consider gpt-4 for better quality if available
                                            messages=[
                                                {"role": "system", "content": get_translation("You are an AI assistant specialized in summarizing and extracting smart questions.")},
                                                {"role": "user", "content": prompt}
                                            ]
                                        )
                                        st.session_state.document_summary[filename] = response.choices[0].message.content
                                        if len(document_text) > MAX_CHUNK_CHARS:
                                            st.session_state.document_summary[filename] = (
                                                get_translation("This document is large and has been split into chunks for analysis.") +
                                                "\n\n" + st.session_state.document_summary[filename]
                                            )

                                except OpenAIError as e:
                                    st.error(f"{get_translation('Summary generation error for')} {filename}: {str(e)}")
                                except Exception as e:
                                    st.error(f"{get_translation('Summary generation error for')} {filename}: An unexpected error occurred - {str(e)}")

                    else:
                        st.warning(get_translation("OpenAI API key is not available. Cannot generate summary."))

                    except Exception as e:
                        # Catch errors during file reading or initial processing
                        st.error(f"{get_translation('Error during document processing for')} {filename}: {str(e)}")

# --- SHOW SUMMARIES ---
# Display summaries if available in session state
if st.session_state.document_summary:
    st.subheader(get_translation("📄 Summaries & Smart Questions"))
    for fname, summary in st.session_state.document_summary.items():
        st.markdown(f"**🗂️ {fname}**")
        # Escape markdown characters to display summary raw
        escaped_summary = summary.replace("#", "\\#").replace("*", "\\*").replace("_", "\\_").replace("`", "\\`").replace("[", "\\[").replace("]", "\\]")
        st.markdown(escaped_summary)
        st.markdown(get_translation("---")) # Separator

# --- CHAT INTERFACE ---
st.subheader(get_translation("🗣️ Ask Questions Based on the Documents"))
chat_container = st.container() # Container to hold chat messages, allows easy clearing/scrolling

# Form for user chat input
with st.form("chat_input_form", clear_on_submit=True):
    # Use columns for input text and send button
    col1, col2 = st.columns([9, 1])
    with col1:
        # Text input for user's question
        user_input = st.text_input(get_translation("Ask anything about the uploaded documents..."), key="user_input")
    with col2:
        # Add a bit of vertical space to align button
        st.markdown("<div>&nbsp;</div>", unsafe_allow_html=True)
        # Submit button for the form
        submitted = st.form_submit_button(get_translation("Send"), use_container_width=True)

    # Handle form submission
    if submitted and user_input:
        # Check if documents have been processed
        if not st.session_state.document_chunks:
            st.warning(get_translation("Please upload documents before asking questions."))
        # Check if API key is available for chat
        elif not openai_api_key:
            st.warning(get_translation("OpenAI API key is not available. Cannot answer questions."))
        else:
            # Prepare document context for the LLM by joining chunks (up to MAX_CHUNK_CHARS)
            all_chunks = [chunk for chunk_list in st.session_state.document_chunks.values() for chunk in chunk_list]
            combined_chunks_text = ""
            for chunk in all_chunks:
                # Add chunk if it fits within the MAX_CHUNK_CHARS limit
                if len(combined_chunks_text) + len(chunk) + 2 <= MAX_CHUNK_CHARS: # +2 for potential \n\n
                     if combined_chunks_text:
                         combined_chunks_text += "\n\n" + chunk
                     else:
                         combined_chunks_text = chunk
                else:
                    break # Stop adding chunks if the limit is reached

            if not combined_chunks_text:
                 st.warning("No document content available or chunks are too large.") # Should not happen if documents were processed

            # Construct the chat prompt with document context and user question
            prompt_chat = f"""
{get_translation("You are a helpful AI assistant designed to answer questions based on the provided documents.\nAnalyze the following documents and answer the user's question as accurately and concisely as possible.\nIf the answer is not explicitly found in the documents, state that you cannot find the answer.")}

{get_translation("Documents:")}
{combined_chunks_text}

{get_translation("Question:")} {user_input}
"""
            try:
                # Add user message to history immediately
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                # Use st.status for ongoing process feedback
                with st.status("Generating response...", expanded=True) as status:
                    status.update(label="Sending query to AI...", state="running")
                    client = openai.OpenAI(api_key=openai_api_key)
                    response_chat = client.chat.completions.create(
                        model="gpt-3.5-turbo", # Consider gpt-4 for better quality
                        messages=[
                            # Include chat history for context in conversation (optional, but good for persistent chat)
                            # Be mindful of token limits with long history
                            {"role": "system", "content": get_translation("You are an AI assistant that answers questions based on provided documents.")},
                            # Append previous chat history, excluding system messages
                            *[{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_history[-10:] if m["role"] != "system"], # Include last 10 messages for context
                            {"role": "user", "content": prompt_chat} # The current query including document context
                        ]
                    )
                    assistant_response = response_chat.choices[0].message.content
                    # Append assistant's response to history
                    st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
                    status.update(label="Response received!", state="complete", icon="✅")

                except OpenAIError as e:
                status.update(label="Error!", state="error", icon="❌")
                    st.error(f"{get_translation('Error during chat completion:')} {str(e)}")
            except Exception as e:
                status.update(label="Error!", state="error", icon="❌")
                st.error(f"{get_translation('Error during chat completion:')} An unexpected error occurred - {str(e)}")


# --- DISPLAY CHAT HISTORY ---
# Display chat messages in the chat container
if st.session_state.chat_history:
    with chat_container:
        st.subheader(get_translation("💬 Chat History")) # Add subheader here
        for message in st.session_state.chat_history:
            # Use st.chat_message for standard chat bubble styling
            with st.chat_message(message["role"]):
                # Display role and content (role capitalized and translated)
                st.markdown(f"**{get_translation(message['role'].capitalize())}:** {message['content']}")

    # Optional: Add JavaScript to attempt scrolling to the bottom of the chat history
    # Note: This relies on internal Streamlit class names which might change
    js = f"""
        <script>
            function scrollChatToBottom() {{
                // Find the element containing the chat messages - class name might vary
                const chatContainer = document.querySelector('[data-testid="chat-messages"]');
                if (chatContainer) {{
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }}
            }}
            // Use a slight delay to ensure elements are rendered
            setTimeout(scrollChatToBottom, 100);
        </script>
        """
    st.components.v1.html(js, height=0, width=0) # Embed the JS, hide the component output


# --- DOWNLOAD REPORT ---
# Provide a download link for the report if there's content
if st.session_state.chat_history or st.session_state.document_summary:
    # Build the report content string
    report_text = f"{get_translation('# DeloitteSmart™ AI Assistant Report')}\n\n"

    if st.session_state.document_summary:
        report_text += f"{get_translation('## Document Summaries')}:\n"
        for fname, summary in st.session_state.document_summary.items():
            report_text += f"### {fname}\n{summary}\n\n"

    if st.session_state.chat_history:
        report_text += f"\n{get_translation('## Chat History')}:\n"
        for chat in st.session_state.chat_history:
            report_text += f"**{get_translation(chat['role'].capitalize())}:** {chat['content']}\n\n"

    # Function to create the download link (text file)
    def create_download_link(report):
        buffer = BytesIO()
        buffer.write(report.encode("utf-8"))
        buffer.seek(0)
        # Encode report content to base64 for embedding in the link
        b64 = base64.b64encode(buffer.getvalue()).decode()
        href = f'data:text/plain;base64,{b64}'
        # Generate a filename based on current time
        filename = f"deloitte_smart_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        return f'<a href="{href}" download="{filename}">{get_translation("Download Report")}</a>'

    st.markdown(get_translation("---")) # Separator
    st.subheader(get_translation("⬇️ Download Report"))
    # Display the generated download link
    st.markdown(create_download_link(report_text), unsafe_allow_html=True)

# --- FEEDBACK SECTION ---
st.markdown(get_translation("---")) # Separator
st.subheader(get_translation("📝 Feedback"))
# Text area for user feedback
feedback_text = st.text_area(
    get_translation("Share your feedback to help us improve:"),
    key="feedback_input", # Key for session state
    height=100
)
# Button to submit feedback
if st.button(get_translation("Submit Feedback")):
    if feedback_text:
        # Store feedback with timestamp
        feedback_entry = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "feedback": feedback_text}
        st.session_state.feedback.append(feedback_entry)
        st.success(get_translation("Thank you for your feedback!"))
        # Clear the feedback text area after submission
        st.session_state.feedback_input = "" # Clear the widget via its key
    else:
        st.warning(get_translation("Please enter your feedback."))

# Display submitted feedback
if st.session_state.feedback:
    st.subheader(get_translation("📬 Submitted Feedback"))
    for fb in st.session_state.feedback:
        st.markdown(f"**{get_translation('Timestamp')}:** {fb['timestamp']}")
        st.markdown(fb['feedback'])
        st.markdown(get_translation("---")) # Separator for feedback entries
