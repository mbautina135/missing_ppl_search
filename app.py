# main.py

import streamlit as st
from google.cloud import storage

from bucket_operations import read_files_from_bucket
from vertexai.generative_models import GenerativeModel
from google_map import prepare_data_from_polygons, render_google_map
from config import load_config, initialize_credentials
from chat_module import render_chat
from ui import define_css, render_sidebar
from map_operations import update_zone


def initialize_client():
    """
    Initializes the Google Cloud Storage client.
    """
    try:
        client = storage.Client()
        return client
    except Exception as e:
        st.error(f"Failed to initialize Google Cloud Storage client: {e}")
        return None

def initialize_chat_session():
    """Initialize the session state for the chat if not already initialized."""
    if "messages" not in st.session_state:
        config = load_config()
        person_info, updates, _ = read_files_from_bucket(config,config.get("bucket_name", ""),'person1234')
        st.session_state.messages = []
        prompt = """You are a highly intelligent and supportive tool designed to assist volunteers in finding missing persons. Your role is to provide critical information, facilitate collaboration, and offer relevant insights to make the search as efficient as possible.
                        When volunteers start their session, greet them warmly, introduce yourself as their partner in this search effort (digital assistant without a name), and provide the details about the missing person, ensuring they understand the gravity of the situation and your capabilities.
                        Let volunteers know that they can find the most recent activity, updates, and related news in the sidebar to assist them in their search.
                        Encourage volunteers to share with you any new updates, findings, or ideas directly into the chat. Inform them that all updates will be visible to other volunteers, fostering teamwork and ensuring no critical detail is overlooked.
                        Make your tone supportive and encouraging to motivate them during this important mission. Try to be concise. 
                        Information about the person:\n""" + person_info + """
                        Based on the most recent updates you have provide a few recommendations where to search etc. Updates:\n""" + str(updates)
        model = GenerativeModel(model_name=config.get("llm_id", "gemini-1.5-pro"))
        chat = model.start_chat(response_validation=False)
        response = chat.send_message(prompt)
        parts = response.candidates[0].content.parts
        response = "".join(part.text for part in parts
            if hasattr(part, 'text') and part.text)
        st.session_state.messages.append({"is_user": False, "text": response})

def main():
    """
    Main function to run the Streamlit app.
    """
    st.set_page_config(
        page_title="Map and Chat",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.markdown(
    """
    <style>
        /* Set the sidebar width to 30% of the screen */
        [data-testid="stSidebar"] {
            width: 30%;
            min-width: 30%;
            max-width: 30%;
        }
        [data-testid="stSidebarHeader"] {
    display: none;
}
        /* Disable resizing of the sidebar */
        [data-testid="stSidebar"] .block-container {
            resize: none;
        }

        /* Remove blank space at top and bottom */
        .block-container {
            padding-top: 0rem;
            padding-bottom: 0rem;
        }

        /* Adjust center canvas position */
        .st-emotion-cache-z5fcl4 {
            position: relative;
            top: -62px;
        }

        /* Customize toolbar and content visibility */
        .st-emotion-cache-18ni7ap {
            pointer-events: none;
            background: rgba(255, 255, 255, 0%);
        }
        .st-emotion-cache-zq5wmm {
            pointer-events: auto;
            background: rgb(255, 255, 255);
            border-radius: 5px;
        }

        /* Remove top padding/margin */
        .main {
            padding-top: 0px !important;
            padding-bottom: 0px !important;
        }

        /* Hide the Streamlit header */
        header {
            visibility: hidden;
        }

        /* Make sidebar non-collapsible by hiding the collapse button */
        [data-testid="stSidebarNav"] {
            display: none;
        }

        /* Hide the arrow toggle button at the top of the sidebar */
        [data-testid="stSidebarToggle"] {
            display: none;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


    # Define and inject CSS
    define_css()

    if 'upload_key' not in st.session_state:
        st.session_state['upload_key'] = 0

    # Load configuration
    config = load_config()
    if not config:
        return

    # Initialize credentials and AI Platform
    if not initialize_credentials(config):
        return

    # Initialize session state variables
    if 'pins' not in st.session_state:
        st.session_state['pins'] = []
    if 'pending_news' not in st.session_state:
        st.session_state['pending_news'] = True
    if 'last_green' not in st.session_state:
        st.session_state['last_green'] = False

    if "zones" not in st.session_state:
        try:
            zones = prepare_data_from_polygons('data/SF_Find_Neighborhoods_20241121.csv')
            st.session_state["zones"] = zones
        except:
            pass
    initial_zone_state = {("Mission","Searched","Elliot Grayson"),
                          ("Potrero Hill","Searched","Elliot Grayson"),
                          ("Produce Market","Searched","Lucas Finch"),
                          ("Showplace Square",'In Progress',"Lucas Finch"),
                          ("Oceanview","Searched","Lucas Finch"),
                          ("Cayuga",'In Progress',"Nathaniel Hayes"),
                          ("Mission Terrace",'In Progress',"Nathaniel Hayes"),
                          ("Sunnyside",'In Progress',"Nathaniel Hayes"),
                          ("Westwood Park",'In Progress',"Nathaniel Hayes"),
                          ("Golden Gate Park", "Searched","Evelyn Carrington"),
                           ("Ingleside","Searched","Evelyn Carrington")}
    for item in initial_zone_state:
        update_zone(st.session_state.zones,item[0], item[1],item[2])
    #'Available', 'In Progress', 'Searched'

    # Initialize chat session
    initialize_chat_session()

    # Render sidebar (includes toggle buttons and chat)
    render_sidebar(config)
        
    map_placeholder = st.empty()
    
    render_google_map(
        zones = st.session_state["zones"],
        pins=st.session_state.get('pins', []),
        api_key=st.session_state.get("api_key", ""),
        map_placeholder=map_placeholder
    )

    render_chat(config)


if __name__ == "__main__":
    main()
