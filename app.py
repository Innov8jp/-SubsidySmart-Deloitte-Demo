# DeloitteSmart™ AI Assistant – Full Version (Enhanced Multi-Doc Summarizer, Persistent Chat, Feedback, Downloadable Report - No Actual OCR)



import streamlit as st

import openai

import fitz  # PyMuPDF

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



# --- LANGUAGE TOGGLE AND TRANSLATION FUNCTION ---

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

        "📸 Capture Image for Testing (Demo Only)": "📸 テスト用の画像をキャプチャ (デモのみ)",

        "Take a picture": "写真を撮る",

        "Captured Image": "キャプチャされた画像",

        "✅ Image captured. In this demo version, OCR is not applied.": "✅ 画像をキャプチャしました。このデモ版では、OCRは適用されません。",

        "Thank you for uploading a photo. In the full version, text would be extracted and summarized here.": "写真のアップロードありがとうございます。フルバージョンでは、ここでテキストが抽出され、要約されます。",

        "camera_demo_": "camera_demo_",

        "✅ Demo summary and questions have been added from captured image.": "✅ デモの要約と質問が、キャプチャされた画像から追加されました。",

    }

    return translations.get(english_text, english_text) if language == "日本語" else english_text



# --- SIDEBAR ---

with st.sidebar:

    st.image("deloitte_logo.png", width=200)

    openai_api_key = st.secrets.get("OPENAI_API_KEY")

    if openai_api_key:

        st.sidebar.success(get_translation("✅ OpenAI API key is pre-configured."))

    else:

        st.sidebar.error(get_translation("❌ OpenAI API key not found."))

    st.sidebar.markdown(get_translation("Powered by [Innov8]"))

    st.sidebar.markdown(get_translation("Prototype Version 1.0"))

    st.sidebar.markdown(get_translation("Secure | Scalable | Smart"))



# --- SESSION STATE SETUP ---

session_defaults = {

    "chat_history": [],

    "user_question": "",

    "feedback": [],

    "document_content": {},

    "document_summary": {},

    "uploaded_filenames": []

}

for key, default in session_defaults.items():

    if key not in st.session_state:

        st.session_state[key] = default



# --- TITLE ---

st.title(get_translation("DeloitteSmart™: Your AI Assistant for Faster, Smarter Decisions"))



# --- FILE UPLOAD ---

with st.expander(get_translation("📁 Upload Documents (PDF, TXT)")):

    uploaded_files = st.file_uploader(get_translation("Upload Files"), type=["pdf", "txt"], accept_multiple_files=True)

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

                        try:

                            prompt = f"{get_translation('You are a highly trained consultant. Summarize the following content and generate 5 smart questions.')}\n\n{get_translation('Document:')}\n{st.session_state.document_content[filename]}"

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

                        st.warning(get_

get_translation("OpenAI API key is not available. Cannot generate summary."))

                except Exception as e:

                    st.error(f"{get_translation('PDF extraction error for')} {filename}: {str(e)}")



# --- SHOW SUMMARIES ---

if st.session_state.document_summary:

    st.subheader(get_translation("📄 Summaries & Smart Questions"))

    for fname, summary in st.session_state.document_summary.items():

        st.markdown(f"**🗂️ {fname}**")

        escaped_summary = summary.replace("#", "\\#").replace("*", "\\*").replace("_", "\\_").replace("`", "\\`").replace("[", "\\[").replace("]", "\\]")

        st.markdown(escaped_summary)

        st.markdown(get_translation("---"))



# --- CHAT INTERFACE ---

st.subheader(get_translation("🗣️ Ask Questions Based on the Documents"))

chat_container = st.container() # Container for chat messages



with st.form("chat_input_form", clear_on_submit=True):

    col1, col2 = st.columns([9, 1]) # Adjust column widths to give more space to the input

    with col1:

        user_input = st.text_input(get_translation("Ask anything about the uploaded documents..."), key="user_input")

    with col2:

        st.markdown("<div>&nbsp;</div>", unsafe_allow_html=True) # Add some vertical space

        submitted = st.form_submit_button(get_translation("Send"), use_container_width=True) # Make button fill the column



    if submitted and user_input:

        if not st.session_state.document_content:

            st.warning(get_translation("Please upload documents before asking questions."))

        elif openai_api_key:

            combined_docs = "\n\n".join(st.session_state.document_content.values())

            prompt_chat = f"""

{get_translation("You are a helpful AI assistant designed to answer questions based on the provided documents.\nAnalyze the following documents and answer the user's question as accurately and concisely as possible.\nIf the answer is not explicitly found in the documents, state that you cannot find the answer.")}



{get_translation("Documents:")}

{combined_docs}



{get_translation("Question:")} {user_input}

"""

            try:

                client = openai.OpenAI(api_key=openai_api_key)

                response_chat = client.chat.completions.create(

                    model="gpt-3.5-turbo",

                    messages=[

                        {"role": "system", "content": get_translation("You are an AI assistant that answers questions based on provided documents.")},

                        {"role": "user", "content": prompt_chat}

                    ]

                )

                assistant_response = response_chat.choices[0].message.content

                st.session_state.chat_history.append({"role": "user", "content": user_input})

                st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})

            except OpenAIError as e:

                st.error(f"{get_translation('Error during chat completion:')} {str(e)}")

        else:

            st.warning(get_translation("OpenAI API key is not available. Cannot answer questions."))



# --- DISPLAY CHAT HISTORY ---

if st.session_state.chat_history:

    with chat_container:

        for message in st.session_state.chat_history:

            with st.chat_message(message["role"]):

                st.markdown(f"**{get_translation(message['role'].capitalize())}:** {message['content']}")



    # Scroll to the bottom of the chat container

    js = f"""

        function scrollChatToBottom() {{

            const chatContainer = document.querySelector(".st-emotion-cache-r421ms");

            if (chatContainer) {{

                chatContainer.scrollTop = chatContainer.scrollHeight;

            }}

        }}

        scrollChatToBottom();

        """

    st.components.v1.html(f"<script>{js}</script>")



# --- DOWNLOAD REPORT ---

if st.session_state.chat_history and st.session_state.document_summary:

    report_text = f"# DeloitteSmart™ AI Assistant Report\n\n## {get_translation('Document Summaries')}:\n"

    for fname, summary in st.session_state.document_summary.items():

        report_text += f"### {fname}\n{summary}\n\n"

    report_text += f"\n## {get_translation('Chat History')}:\n"

    for chat in st.session_state.chat_history:

        report_text += f"**{get_translation(chat['role'].capitalize())}:** {chat['content']}\n\n"



    def create_download_link(report):

        buffer = BytesIO()

        buffer.write(report.encode("utf-8"))

        buffer.seek(0)

        b64 = base64.b64encode(buffer.getvalue()).decode()

        href = f'data:text/plain;base64,{b64}'

        filename = f"deloitte_smart_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        return f'<a href="{href}" download="{filename}">{get_translation("Download Report")}</a>'



    st.markdown("---")

    st.subheader(get_translation("⬇️ Download Report"))

    st.markdown(create_download_link(report_text), unsafe_allow_html=True)



# --- FEEDBACK SECTION ---

st.markdown("---")

st.subheader(get_translation("📝 Feedback"))

feedback_text = st.text_area(get_translation("Share your feedback to help us improve:"), key="feedback_input", height=100)

if st.button(get_translation("Submit Feedback")):

    if feedback_text:

        feedback_entry = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "feedback": feedback_text}

        st.session_state.feedback.append(feedback_entry)

        st.success(get_translation("Thank you for your feedback!"))

        st.session_state.feedback_input = ""

    else:

        st.warning(get_translation("Please enter your feedback."))



if st.session_state.feedback:

    st.subheader(get_translation("📬 Submitted Feedback"))

    for fb in st.session_state.feedback:

        st.markdown(f"**{get_translation('Timestamp')}:** {fb['timestamp']}")

        st.markdown(fb['feedback'])

        st.markdown("---")

**Smart Questions:**
1. What is the document about?
2. Who is the target audience?
3. What actions are recommended?
4. Is any regulatory compliance mentioned?
5. What funding or budget is required?"""
    st.session_state.uploaded_filenames.append(cam_doc_name)
    st.success("✅ Demo summary and questions have been added from captured image.")
# --- CONTINUED QUESTION INPUT ---
combined_docs = "

".join(st.session_state.document_content.values())
