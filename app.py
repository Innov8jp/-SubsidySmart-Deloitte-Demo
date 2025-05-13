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
import time # Import time for potential delays/sleep (optional, but good for spinners)

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
        st.sidebar.success(get_translation("✅ OpenAI API key is pre-configured."))
    else:
        st.sidebar.error(get_translation("❌ OpenAI API key not found."))
    st.sidebar.markdown(get_translation("Powered by [Innov8]"))
    st.sidebar.markdown(get_translation("Prototype Version 1.0"))
    st.sidebar.markdown(get_translation("Secure | Scalable | Smart"))

# --- SESSION STATE SETUP ---
# Initialize session state variables if they don't exist
session_defaults = {
    "chat_history": [],  # Stores the chat conversation [{"role": "user", "content": "..."}]
    "user_question": "", # Temporary storage for user input form
    "feedback": [],      # Stores submitted feedback
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

# --- FILE UPLOAD WIDGET ---
# Put just the uploader widget inside the expander
with st.expander(get_translation("📁 Upload Documents (PDF, TXT)")):
    uploaded_files = st.file_uploader(
        get_translation("Upload Files"),
        type=["pdf", "txt"],
        accept_multiple_files=True,
        key="file_uploader" # Added a key for reliable state management
    )

# --- DOCUMENT PROCESSING LOGIC (OUTSIDE EXPANDER) ---
# This block runs after the file_uploader and processes the files
if uploaded_files:
    for file in uploaded_files:
        filename = file.name
        # Check if file has already been processed in this session
        if filename not in st.session_state.uploaded_filenames:
            st.session_state.uploaded_filenames.append(filename)

            document_text = ""
            try:
                # Add a spinner while processing each file
                with st.spinner(f"{get_translation('Processing document')} {filename}..."):
                    file_bytes = file.getvalue() # Use getvalue() for BytesIO like object

                    # 1. Extract Text
                    with st.status(f"{get_translation('Extracting text from')} {filename}...", expanded=False) as status:
                        try:
                            if file.type == "application/pdf":
                                # Use BytesIO to read PDF from bytes
                                with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                                    for page in doc:
                                        document_text += page.get_text() + "\n\n" # Add newline separation between pages
                            elif file.type == "text/plain":
                                document_text = file_bytes.decode("utf-8")
                            status.update(label=f"{get_translation('Extracting text from')} {filename}... Complete.", state="complete", icon="✅")
                        except Exception as e:
                            status.update(label=f"{get_translation('Extracting text from')} {filename}... Failed.", state="error", icon="❌")
                            st.error(f"{get_translation('Error during document processing for')} {filename}: Text extraction failed - {str(e)}")
                            document_text = "" # Clear text if extraction fails
                            # Continue processing this file, just mark text as empty

                    st.session_state.document_content[filename] = document_text.strip() # Store full content

                    if not document_text.strip():
                        st.warning(f"{get_translation('No text extracted from')} {filename}.")
                        st.session_state.document_chunks[filename] = [] # Ensure chunks list is empty
                        st.session_state.document_summary[filename] = f"Could not extract text from {filename}."
                        # Don't continue here, allow summary/chunking logic below to run and handle empty text

                    # 2. Split Document into Chunks (Only if text was extracted)
                    if document_text.strip():
                         with st.status(f"{get_translation('Splitting into chunks:')} {filename}...", expanded=False) as status:
                              try:
                                 st.session_state.document_chunks[filename] = split_text_into_chunks(
                                     document_text, chunk_size=SPLIT_CHUNK_SIZE
                                 )
                                 status.update(label=f"{get_translation('Splitting into chunks:')} {filename}... Complete.", state="complete", icon="✅")
                              except Exception as e:
                                 status.update(label=f"{get_translation('Splitting into chunks:')} {filename}... Failed.", state="error", icon="❌")
                                 st.error(f"{get_translation('Error during document processing for')} {filename}: Chunking failed - {str(e)}")
                                 # Fallback: if chunking fails, use the beginning of the text as a single chunk (up to context limit)
                                 st.session_state.document_chunks[filename] = [document_text[:MAX_CONTEXT_CHARS]]
                                 st.session_state.document_summary[filename] = f"Chunking failed for {filename}. Using limited text for summary."
                    else:
                         # If no text extracted, ensure chunks are empty
                         st.session_state.document_chunks[filename] = []


                    # 3. Summarize if API key is available (Only if text or fallback text exists)
                    if openai_api_key:
                        # Use the full text for summarization if it's reasonably small,
                        # otherwise use the first few chunks. Summarizing based on chunks
                        # for very large documents can lose overall context.
                        # Use original document_text for size check
                        summary_text_source = document_text if len(document_text) < MAX_CONTEXT_CHARS * 2 else " ".join(st.session_state.document_chunks.get(filename, [])[:5]) # Use first 5 chunks if very large, handle missing filename in chunks

                        if summary_text_source.strip():
                            with st.status(f"{get_translation('Generating summary and questions for')} {filename}...", expanded=True) as status:
                                try:
                                    prompt = f"{get_translation('You are a highly trained consultant. Summarize the following content and generate 5 smart questions.')}\n\n{get_translation('Document:')}\n{summary_text_source}"
                                    client = openai.OpenAI(api_key=openai_api_key)
                                    response = client.chat.completions.create(
                                        model="gpt-3.5-turbo", # Consider gpt-4 for potentially better quality/larger context
                                        messages=[
                                            {"role": "system", "content": get_translation("You are an AI assistant specialized in summarizing and extracting smart questions.")},
                                            {"role": "user", "content": prompt}
                                        ]
                                    )
                                    summary_content = response.choices[0].message.content
                                    if len(document_text) >= MAX_CONTEXT_CHARS * 2: # Check against original text size
                                        summary_content = (
                                            get_translation("Note: This document is large and analysis uses chunks, which may impact summary/answer accuracy.") +
                                            "\n\n" + summary_content
                                        )
                                    st.session_state.document_summary[filename] = summary_content
                                    status.update(label=f"{get_translation('Generating summary and questions for')} {filename}... Complete.", state="complete", icon="✅")

                                except OpenAIError as e:
                                    status.update(label=f"{get_translation('Generating summary and questions for')} {filename}... Failed.", state="error", icon="❌")
                                    st.error(f"{get_translation('Summary generation error for')} {filename}: {str(e)}")
                                except Exception as e:
                                    status.update(label=f"{get_translation('Generating summary and questions for')} {filename}... Failed.", state="error", icon="❌")
                                    st.error(f"{get_translation('Summary generation error for')} {filename}: An unexpected error occurred - {str(e)}")
                        else:
                            # Case where summary_text_source was empty after potentially using first chunks
                            st.session_state.document_summary[filename] = f"Could not generate summary for {filename} (text source was empty)."
                            st.warning(f"Could not generate summary for {filename} (text source was empty).")


                    else:
                        # Handle case where API key is missing
                        st.warning(get_translation("OpenAI API key is not available. Cannot generate summary."))
                        st.session_state.document_summary[filename] = get_translation("Summary generation skipped (API key missing).")

            except Exception as e:
                # Catch any other errors during file reading or initial processing not caught within status blocks
                st.error(f"{get_translation('Error during document processing for')} {filename}: An unexpected error occurred - {str(e)}")


# --- SHOW SUMMARIES ---
# Display summaries if available in session state
if st.session_state.document_summary:
    st.subheader(get_translation("📄 Summaries & Smart Questions"))
    for fname, summary in st.session_state.document_summary.items():
        st.markdown(f"**🗂️ {fname}**")
        # Escape markdown characters to display summary raw
        # This prevents issues if the summary itself contains markdown like #, *, etc.
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
        # Check if documents have been processed and chunks are available
        all_chunks = [chunk for chunk_list in st.session_state.document_chunks.values() for chunk in chunk_list]
        if not all_chunks:
            st.warning(get_translation("Please upload documents before asking questions."))
        # Check if API key is available for chat
        elif not openai_api_key:
            st.warning(get_translation("OpenAI API key is not available. Cannot answer questions."))
        else:
            # Prepare document context for the LLM by joining chunks (up to MAX_CONTEXT_CHARS)
            combined_chunks_text = ""
            for chunk in all_chunks:
                # Add chunk if it fits within the MAX_CONTEXT_CHARS limit (+2 for potential \n\n)
                if len(combined_chunks_text) + len(chunk) + 2 <= MAX_CONTEXT_CHARS:
                    if combined_chunks_text:
                         combined_chunks_text += "\n\n" + chunk
                    else:
                         combined_chunks_text = chunk
                else:
                    break # Stop adding chunks if the limit is reached

            if not combined_chunks_text:
                 st.warning(get_translation("No document content available or chunks are too large to fit in context."))
                 # Add user message to history anyway, indicating no doc context was used
                 st.session_state.chat_history.append({"role": "user", "content": user_input})
                 # Optionally add an assistant message explaining the lack of context
                 st.session_state.chat_history.append({"role": "assistant", "content": get_translation("I couldn't use the document content for this question due to formatting or size issues.")})

            else: # Proceed with AI call if context text was successfully created
                # Add user message to history immediately
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                # Use st.status for ongoing process feedback
                with st.status(get_translation("Generating response..."), expanded=True) as status:
                    status.update(label=get_translation("Sending query to AI..."), state="running")
                    try:
                        client = openai.OpenAI(api_key=openai_api_key)
                        response_chat = client.chat.completions.create(
                            model="gpt-3.5-turbo", # Consider gpt-4 for potentially better quality
                            messages=[
                                # System message defining the AI's role and instructions
                                {"role": "system", "content": get_translation("You are a helpful AI assistant designed to answer questions based on the provided documents.\nAnalyze the following documents and answer the user's question as accurately and concisely as possible.\nIf the answer is not explicitly found in the documents, state that you cannot find the answer.")},
                                # Append relevant previous chat history for context (e.g., last 10 non-system messages)
                                # This helps the AI understand follow-up questions.
                                *[{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_history[-11:-1] if m["role"] != "system"], # Exclude the *current* user message and system messages
                                # The current user's question, including the document context
                                {"role": "user", "content": f"{get_translation('Documents:')}\n{combined_chunks_text}\n\n{get_translation('Question:')} {user_input}"}
                            ]
                        )
                        assistant_response = response_chat.choices[0].message.content
                        # Append assistant's response to history
                        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
                        status.update(label=get_translation("Response received!"), state="complete", icon="✅")

                    except OpenAIError as e:
                        # More specific error handling for OpenAI issues
                        status.update(label=get_translation("Error!"), state="error", icon="❌")
                        st.error(f"{get_translation('Error during chat completion:')} {str(e)}")
                    except Exception as e:
                        # Catch any other unexpected errors during the API call process
                        status.update(label=get_translation("Error!"), state="error", icon="❌")
                        st.error(f"{get_translation('Error during chat completion:')} An unexpected error occurred - {str(e)}")


# --- DISPLAY CHAT HISTORY ---
# Display chat messages in the chat container
if st.session_state.chat_history:
    with chat_container:
        st.subheader(get_translation("💬 Chat History")) # Add subheader here
        # Display messages using Streamlit's chat_message container
        for message in st.session_state.chat_history:
            # Skip system messages from display, they are for the AI
            if message["role"] != "system":
                with st.chat_message(message["role"]):
                    # Display role and content (role capitalized and translated)
                    display_role = get_translation(message['role'].capitalize())
                    st.markdown(f"**{display_role}:** {message['content']}")

    # Optional: Add JavaScript to attempt scrolling to the bottom of the chat history
    # Note: This relies on internal Streamlit element attributes which might change.
    # height=0 and width=0 hide the component itself.
    js = """
    <script>
        function scrollChatToBottom() {
            // Find the element containing the chat messages - using a reliable data-testid
            const chatContainer = document.querySelector('[data-testid="stVerticalBlock"]'); // This might target a parent block containing messages
            // More specific target might be needed depending on Streamlit version/structure
            // const chatMessages = document.querySelector('[data-testid="chat-messages"]'); // This test id might not always exist/be reliable

            if (chatContainer) {
                // Attempt to find the scrollable element within or is the container itself
                const scrollableElement = chatContainer.parentElement; // Often the parent is the scrollable one
                if (scrollableElement) {
                   scrollableElement.scrollTop = scrollableElement.scrollHeight;
                } else {
                   // Fallback to the container itself if parent is not scrollable
                   chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            }
        }
        // Use a slight delay to ensure elements are rendered before scrolling
        setTimeout(scrollChatToBottom, 100);
    </script>
    """
    st.components.v1.html(js, height=0, width=0)


# --- DOWNLOAD REPORT ---
# Provide a download link for the report if there's content to report
if st.session_state.chat_history or st.session_state.document_summary:
    # Build the report content string
    report_text = f"{get_translation('# DeloitteSmart™ AI Assistant Report')}\n\n"

    if st.session_state.document_summary:
        report_text += f"{get_translation('## Document Summaries')}:\n\n" # Added extra newline
        for fname, summary in st.session_state.document_summary.items():
            # Clean up potential markdown escapes for the raw text file
            cleaned_summary = summary.replace("\\#", "#").replace("\\*", "*").replace("\\_", "_").replace("\\`", "`").replace("\\[", "[").replace("\\]", "]")
            report_text += f"### {fname}\n{cleaned_summary}\n\n" # Use cleaned summary for report

    if st.session_state.chat_history:
        report_text += f"\n{get_translation('## Chat History')}:\n\n" # Added extra newline
        for chat in st.session_state.chat_history:
            # Only include user and assistant messages in the report
            if chat["role"] in ["user", "assistant"]:
                 report_text += f"**{get_translation(chat['role'].capitalize())}:** {chat['content']}\n\n"

    # Function to create the download link (text file)
    # This encodes the text content into a base64 string for the download link.
    def create_download_link(report):
        buffer = BytesIO()
        buffer.write(report.encode("utf-8"))
        buffer.seek(0)
        # Encode report content to base64 for embedding in the link
        b64 = base64.b64encode(buffer.getvalue()).decode()
        href = f'data:text/plain;base64,{b64}'
        # Generate a filename based on current time
        filename = f"deloitte_smart_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        # Create the HTML anchor tag with the download attribute
        return f'<a href="{href}" download="{filename}">{get_translation("Download Report")}</a>'

    st.markdown(get_translation("---")) # Separator
    st.subheader(get_translation("⬇️ Download Report"))
    # Display the generated download link using st.markdown with unsafe_allow_html
    st.markdown(create_download_link(report_text), unsafe_allow_html=True)

# --- FEEDBACK SECTION ---
st.markdown(get_translation("---")) # Separator
st.subheader(get_translation("📝 Feedback"))
# Text area for user feedback
feedback_text = st.text_area(
    get_translation("Share your feedback to help us improve:"),
    key="feedback_input", # Key for session state management
    height=100
)
# Button to submit feedback
if st.button(get_translation("Submit Feedback")):
    if feedback_text:
        # Store feedback with timestamp
        feedback_entry = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "feedback": feedback_text}
        st.session_state.feedback.append(feedback_entry)
        st.success(get_translation("Thank you for your feedback!"))
        # Clear the feedback text area after submission using its key
        st.session_state.feedback_input = ""
    else:
        st.warning(get_translation("Please enter your feedback."))

# Display submitted feedback
if st.session_state.feedback:
    st.subheader(get_translation("📬 Submitted Feedback"))
    # Iterate through feedback entries and display them
    for fb in st.session_state.feedback:
        st.markdown(f"**{get_translation('Timestamp')}:** {fb['timestamp']}")
        st.markdown(fb['feedback'])
        st.markdown(get_translation("---")) # Separator for feedback entries
