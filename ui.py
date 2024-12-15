# ui.py
import time
import streamlit as st
from bucket_operations import read_files_from_bucket, read_news_and_combine
import pandas as pd
import base64
from chat_handler import get_llm_response
from llm_tools import tools, get_functions
from vertexai.generative_models import (
    GenerativeModel,
)

def define_css():
    """
    Injects custom CSS into the Streamlit app.
    """
    scrollable_css = """
<style>
/* Scrollable Container Styles */
.scrollable-container {
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    height: 540px;
    padding: 0; /* Remove padding to avoid gaps */
    background-color: #f0f2f6;
    position: relative;
}

.message-block.fixed {
    position: sticky;
    top: 0;
    background-color: #ffffff;
    z-index: 10;
    padding: 15px 20px;
    border: 2px solid #007BFF; /* Blue border */
    border-radius: 8px;
    margin: 0; /* Ensure no margin creates a gap */
    margin-bottom: 10px; 
    box-shadow: 0px 4px 8px rgba(0, 123, 255, 0.3); /* Blue shadow */
    font-size: 14px;
    line-height: 1.5;
    text-align: left;
    transition: box-shadow 0.3s, border-color 0.3s; /* Add smooth transitions */
}

/* Regular Message Blocks */
.message-block {
    background-color: #ffffff;
    border: 2px solid #C0C0C0; /* Silver border */
    border-radius: 8px;
    padding: 15px 20px;
    margin-bottom: 10px;
    box-shadow: 0px 4px 8px rgba(192, 192, 192, 0.5); /* Silver glow */
    box-sizing: border-box;
    font-size: 14px;
    line-height: 1.5;
    text-align: left;
    transition: box-shadow 0.3s, border-color 0.3s; /* Smooth transitions */
}

.message-block2 {
    background-color: #28A745;
    border: 2px solid #C0C0C0; /* Silver border */
    border-radius: 8px;
    padding: 15px 20px;
    margin-bottom: 10px;
    box-shadow: 0px 4px 8px rgba(192, 192, 192, 0.5); /* Silver glow */
    box-sizing: border-box;
    font-size: 14px;
    line-height: 1.5;
    text-align: left;
    transition: box-shadow 0.3s, border-color 0.3s; /* Smooth transitions */
}

/* Image Styling */
.message-block img {
    max-width: 110px;
    max-height: 110px;
    object-fit: cover;
    border: 1px solid #ccc;
}

.message-block.with-photo {
    display: flex;
    align-items: center;
    gap: 20px;
}

.message-block.with-photo .photo {
    flex-shrink: 0;
}

.message-block.with-photo .text-content {
    flex: 1;
}

/* Scrollbar Styling */
.scrollable-container::-webkit-scrollbar {
    width: 8px;
}

.scrollable-container::-webkit-scrollbar-thumb {
    background-color: #c1c1c1;
    border-radius: 4px;
}

.scrollable-container {
    -ms-overflow-style: none;
    scrollbar-width: thin;
}
</style>
"""

    st.markdown(scrollable_css, unsafe_allow_html=True)

def render_sidebar(config):
    """
    Renders the sidebar with toggle buttons, chat, and content based on the selected view.
    """
    with st.sidebar:
        # Initialize 'switcher' in session_state if not present
        if 'switcher' not in st.session_state:
            st.session_state['switcher'] = "Media news"

        # Inject dynamic CSS based on the active switcher state
        if st.session_state['switcher'] == "Media news":
            active_button_css = """
            <style>
            .button-container .toggle-button:nth-child(1) {
                background-color: #4CAF50;
                color: white;
            }
            .button-container .toggle-button:nth-child(2) {
                background-color: #e0e0e0;
                color: #000;
            }
            </style>
            """
        else:
            active_button_css = """
            <style>
            .button-container .toggle-button:nth-child(1) {
                background-color: #e0e0e0;
                color: #000;
            }
            .button-container .toggle-button:nth-child(2) {
                background-color: #4CAF50;
                color: white;
            }
            </style>
            """
        st.markdown(active_button_css, unsafe_allow_html=True)

        render_missing_person(config)
        # Create a container for centering buttons
        st.markdown("<div class='button-container'>", unsafe_allow_html=True)

        # Create two equal-width columns for the toggle buttons without spacer
        toggle_col1, toggle_col2 = st.columns([1, 1])

        with toggle_col1:
            news_clicked = st.button(
                "Media news",
                key="news_btn",
                use_container_width=True
            )
            if news_clicked:
                st.session_state['switcher'] = "Media news"

        with toggle_col2:
            person_clicked = st.button(
                "Person updates",
                key="person_btn",
                use_container_width=True
            )
            if person_clicked:
                st.session_state['switcher'] = "Person updates"

        st.markdown("</div>", unsafe_allow_html=True)

        # Determine which view to show based on 'switcher'
        switcher = st.session_state['switcher']

        if switcher == "Media news":
            render_news_section(st.session_state.pending_news, st.session_state.last_green)
            add_pins_from_news(config)
            
        else:
            render_person_section(config)

def add_pins_from_news(config):
   if 'news' in st.session_state:
        try:
            model = GenerativeModel(
                model_name=config.get("llm_id", "gemini-1.5-pro"), tools=[tools]
            )
        except Exception as e:
            st.error(f"Failed to initialize LLM model: {e}")
            return
        chat = model.start_chat(response_validation=False)
        try:
            for n in st.session_state.news:
                prompt = """You have access to tools to add pins on a map. You will be given the news description.
                            If the input describes an event (excluding search-related updates), determine its approximate location using the best available information, categorize it as either a 'collision', 'robbery' or 'other danger' and add a pin to the map.
                            Act accordingly without asking follow-up questions. News:\n""" + str(n)
                try:
                    response = get_llm_response(prompt, chat, model)
                except Exception as e:
                    st.error(f"Failed to initialize LLM model: {e}")
                    return
                if response and len(response.candidates) > 0 and response.candidates[0].content.parts:
                    function_call = response.candidates[0].content.parts[0].function_call
                    functions = get_functions()
                    if function_call and function_call.name == 'add_pin':
                        function_name = 'add_pin'
                        function_args = function_call.args
                        if function_args:
                            functions[function_name](**function_args)
        except Exception:
            return
        
def render_news_section(pending_news=True, last_green=False):
    """
    Renders the News section in the sidebar.
    """
    messages = read_news_and_combine(st.session_state['config'].get("bucket_name", ""))
    if pending_news:
        messages = messages[0:-1]
    st.session_state['news'] = messages
    messages_html = "<div class='scrollable-container'>"
    for msg in messages:
        if msg == messages[-1] and not pending_news:
            messages_html += f"""<div class='message-block'>
                        <div><strong style="color: green;">New update:</strong> <span style="color: green;">{msg.get('news_name', 'N/A')}</span></div>
                        <div><strong>Source:</strong> {msg.get('source', 'N/A')}</div>
                        <div><strong>Published At:</strong> {msg.get('published_at', 'N/A')}</div>
                        <div><strong>URL:</strong> <a href="{msg.get('url', '#')}" target="_blank">{msg.get('url', 'N/A')}</a></div>
                        <div><strong>Coordinates:</strong> {msg.get('coordinates', 'N/A')}</div>
                        </div>"""
        else:
            messages_html += f"""<div class='message-block'>
            <div><strong>Title:</strong> {msg.get('news_name', 'N/A')}</div>
            <div><strong>Source:</strong> {msg.get('source', 'N/A')}</div>
            <div><strong>Published At:</strong> {msg.get('published_at', 'N/A')}</div>
            <div><strong>URL:</strong> <a href="{msg.get('url', '#')}" target="_blank">{msg.get('url', 'N/A')}</a></div>
            <div><strong>Coordinates:</strong> {msg.get('coordinates', 'N/A')}</div>
            </div>"""
    messages_html += "</div>"

    st.markdown(messages_html, unsafe_allow_html=True)

def render_person_section(config):
    """
    Renders the Person Details section in the sidebar.
    """
    try:
        person_description_html, person_updates, person_photo = read_files_from_bucket(
            config=config,
            bucket_name=config.get("bucket_name", ""),
            folder="person1234"
        )
    except Exception as e:
        st.error(f"Error reading files from S3: {e}")
        person_description_html, person_updates, person_photo = "", [], None
    if 'person_updates' not in st.session_state:
        st.session_state['person_updates'] = person_updates
    messages = person_updates
    messages_html = "<div class='scrollable-container'>"

    # Remaining messages (scrollable)
    for msg in messages[1:]:
        messages_html += f"""<div class='message-block'>
            <div><strong>Date: </strong> {msg[2]}</div>
            <div><strong>Location: </strong> {msg[3]}</div>
            <div><strong>Details: </strong>{msg[4]}</div>
            <div><strong>Volunteer name: </strong> {msg[1]}</div>
            </div>"""
    messages_html += "</div>"

    st.markdown(messages_html, unsafe_allow_html=True)

@st.cache_data
def render_missing_person(config):
    try:
        person_description_html, person_updates, person_photo = read_files_from_bucket(
            config=config,
            bucket_name=config.get("bucket_name", ""),
            folder="person1234"
        )
    except Exception as e:
        st.error(f"Error reading files from S3: {e}")
        person_description_html, person_updates, person_photo = "", [], None

    # Convert photo to base64 if available
    if person_photo:
        base64_photo = base64.b64encode(person_photo).decode('utf-8')
        photo_html = f"<img src='data:image/jpeg;base64,{base64_photo}' alt='Person Photo' style='float: left; margin: 0 15px 15px 0; max-width: 150px; height: auto;' />"
    else:
        photo_html = "<div style='float: left; margin: 0 15px 15px 0; color: red;'>Photo not available</div>"

    def format_text_with_styles(input_text):
        lines = input_text.split('<br>')  # Split text by <br> tags
        formatted_lines = []

        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)  # Split at the first colon
                formatted_line = f"<b style='color:black;'>{key}:</b> <i>{value.strip()}</i>"  # Add bold, color, and italic
            else:
                formatted_line = f"<span style='padding-left:10px;'>{line}</span>"  # Add spacing for non-key-value lines
            formatted_lines.append(formatted_line)

        return '<br>'.join(formatted_lines)  # Add extra spacing between sections

    person_description_html = format_text_with_styles(person_description_html)
    # Styled container
    content_html = f"""
    <div style='
        background-color: #ffffff;
        border: 2px solid #ccc;
        border-radius: 8px;
        padding: 15px;
        width: 100%;
        box-sizing: border-box;
        height: 390px;
        overflow: auto;
        font-size: 14px;
        line-height: 1.5;
        position: relative;
        transition: box-shadow 0.3s, border-color 0.3s;
    '>
        {photo_html}
        <div style='
            overflow: visible;
        '>
            {person_description_html}
        </div>
        <div style='clear: both;'></div>
    </div>
    """
    st.markdown(content_html, unsafe_allow_html=True)

