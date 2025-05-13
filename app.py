# --- SHOW SUMMARIES ---
if st.session_state.document_summary:
    st.subheader(get_translation("📄 Summaries & Smart Questions"))
    for fname, summary in st.session_state.document_summary.items():
        st.markdown(f"#### {get_translation('🗂️')} {fname}")
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
