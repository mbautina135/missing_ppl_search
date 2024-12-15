# chat_module.py

import streamlit as st
import html
import base64
import io
from chat_handler import submit_message


def image_to_base64(image):
    """
    Convert a PIL.Image object to a base64 string.
    """
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")  # Save as PNG (can adjust format as needed)
    return base64.b64encode(buffered.getvalue()).decode()

def render_chat(config):
    if 'upload_key' not in st.session_state:
        st.session_state['upload_key'] = 0

    messages_placeholder = st.empty()

    def on_submit():
        submit_message(config, st.session_state.get('uploaded_file', None))
        st.session_state['upload_key'] += 1
        st.session_state['user_input'] = ""
        st.session_state['uploaded_file'] = None

    with st.container():
        st.markdown("<div class='inputs-container'>", unsafe_allow_html=True)
        st.text_input(
            "Your Message:",
            key="user_input",
            on_change=on_submit,
            placeholder="Type your message here...",
        )
        uploaded_file = st.file_uploader(
            "Upload an image",
            type=["png", "jpg", "jpeg"],
            key=f"file_uploader_{st.session_state['upload_key']}",
            label_visibility="visible"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if uploaded_file:
        st.session_state['uploaded_file'] = uploaded_file

    with messages_placeholder.container():
        st.markdown("<div class='messages-container'>", unsafe_allow_html=True)
        chat_html = """
        <style>
        .chat-container {
            height: 390px;
            overflow-y: auto; 
            border: 1px solid #dcdcdc;
            padding: 10px;
            background-color: #f0f0f0;
            border-radius: 12px;
            margin-bottom: 20px;
            display: flex;
            flex-direction: column;
            box-sizing: border-box;
        }   
        .message {
            padding: 8px 12px;
            margin: 6px 0;
            border-radius: 12px;
            max-width: 75%;
            font-size: 15px;
            line-height: 1.6;
            word-wrap: break-word;
            overflow-wrap: anywhere;
            white-space: pre-wrap;
            font-family: 'Roboto', sans-serif;
        }
        .user-message {
            background-color: #91c9f7; 
            color: white;
            align-self: flex-end;
            box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.1);
        }
        .bot-message {
            background-color: #ffffff;
            color: #2c3e50;
            align-self: flex-start;
            border: 1px solid #e0e0e0;
            box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.1);
        }
        img.message-image {
            max-width: 70%; 
            height: auto; 
            border-radius: 8px;
            margin-top: 5px;
            border: 1px solid #dcdcdc;
        }
        </style>
        <div class="chat-container" id="chat-container">
        """
        if not st.session_state.messages:
            chat_html += '<p style="color: #5f6368; text-align: center; margin: 0;">No messages yet...</p>'
        else:
            for message in st.session_state.messages:
                message_class = 'user-message' if message["is_user"] else 'bot-message'
                message_div = f'<div class="message {message_class}">'
                if message.get("text"):
                    escaped_text = html.escape(message["text"])
                    message_div += f"<p>{escaped_text}</p>"
                if message.get("image"):
                    image_base64 = image_to_base64(message["image"])
                    img_html = f'<img src="data:image/png;base64,{image_base64}" alt="Image" class="message-image"/>'
                    message_div += img_html
                message_div += '</div>'
                chat_html += message_div
        chat_html += """
        </div>
        <script>
        var chatContainer = document.getElementById('chat-container');
        chatContainer.scrollTop = chatContainer.scrollHeight;
        </script>
        """
        st.components.v1.html(chat_html, height=400)
