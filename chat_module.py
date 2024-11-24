import streamlit as st

def initialize_chat_session():
    """Initialize the session state for the chat if not already initialized."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

def display_chat():
    """Display the chat messages in a GCP-styled interface."""
    chat_html = """
    <style>
    .chat-container {
        min-height: 400px;
        max-height: 400px;
        overflow-y: scroll;
        border: 1px solid #e0e0e0;
        padding: 15px;
        background-color: #f5f5f5; /* Light gray GCP-style background */
        border-radius: 12px;
        margin-bottom: 20px;
        display: flex;
        flex-direction: column;
    }
    .message {
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 16px;
        max-width: 75%;
        font-size: 14px;
        line-height: 1.5;
        word-wrap: break-word;
        font-family: 'Roboto', sans-serif; /* GCP-like font */
    }
    .user-message {
        background-color: #1a73e8; /* GCP blue */
        color: white;
        align-self: flex-end;
        box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
    }
    .bot-message {
        background-color: #f1f3f4; /* Light gray for bot messages */
        color: #202124; /* Dark gray text for contrast */
        align-self: flex-start;
        border: 1px solid #dadce0; /* Subtle border */
        box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
    }
    .chat-container::-webkit-scrollbar {
        width: 8px;
    }
    .chat-container::-webkit-scrollbar-thumb {
        background-color: #c0c0c0;
        border-radius: 4px;
    }
    .chat-container::-webkit-scrollbar-thumb:hover {
        background-color: #a0a0a0;
    }
    </style>
    <div class="chat-container">
    """
    if not st.session_state.messages:
        chat_html += '<p style="color: #5f6368; text-align: center;">No messages yet...</p>'
    else:
        for message in st.session_state.messages:
            if message["is_user"]:
                chat_html += f'<div class="message user-message"><b>You:</b> {message["text"]}</div>'
            else:
                chat_html += f'<div class="message bot-message"><b>Bot:</b> {message["text"]}</div>'
    chat_html += "</div>"
    st.markdown(chat_html, unsafe_allow_html=True)

def handle_user_input():
    """Handle user input, add messages to session state, and generate a bot response."""
    user_message = st.session_state.user_input
    if user_message:
        # Add user's message
        st.session_state.messages.append({"is_user": True, "text": user_message})
        # Bot's response logic (simple echo response)
        bot_response = f"You said: {user_message}"
        st.session_state.messages.append({"is_user": False, "text": bot_response})
        # Clear input box
        st.session_state.user_input = ""
