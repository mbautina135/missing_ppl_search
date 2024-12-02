import json
import streamlit as st
from google_map import prepare_data_from_polygons, render_google_map
from chat_module import initialize_chat_session, display_chat, handle_user_input

# Page configuration (set the sidebar to be expanded by default)
st.set_page_config(
    page_title="Map and Chat",
    layout="wide",
    initial_sidebar_state="expanded"
)

def update_zone(zones, zone_name, status, assigned_to=None):
    """
    Update the status and/or assignment of a zone by its name.

    Args:
        zones (list): List of zone dictionaries.
        zone_name (str): The name of the zone to update.
        status (str): New status for the zone.
        assigned_to (str, optional): Person to assign the zone to.

    Returns:
        list: Updated list of zones.
    """
    for zone in zones:
        if zone["name"] == zone_name:
            zone["status"] = status
            if assigned_to:
                zone["assigned_to"] = assigned_to
    return zones

def main():
    # Load config.json
    try:
        with open("config.json") as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        st.error("Configuration file 'config.json' not found.")
        return
    except json.JSONDecodeError:
        st.error("Error decoding 'config.json'. Please check the file format.")
        return

    # Load zones and store in session state
    if "zones" not in st.session_state:
        try:
            zones = prepare_data_from_polygons('SF_Find_Neighborhoods_20241121.csv')
            st.session_state["zones"] = zones
        except FileNotFoundError:
            st.error("CSV file 'SF_Find_Neighborhoods_20241121.csv' not found.")
            return
        except Exception as e:
            st.error(f"An error occurred while preparing data: {e}")
            return

    # Initialize chat session
    initialize_chat_session()

    # List of predefined people for the dropdown
    people = [
        "Alice", "Bob", "Charlie", "Diana", "Eve",
        "Frank", "Grace", "Hank", "Ivy", "Jack"
    ]

    # Centered title for the app using Markdown and HTML
    st.markdown(
        "<h1 style='text-align: center;'>San Francisco Mini Neighborhood Zones and Chat</h1>",
        unsafe_allow_html=True
    )

    # -------------------- Add Scrollable Message Blocks Here -------------------- #

    # Define your messages with 4 sentences each
    messages = [
        (
            "Welcome to the SF Neighborhood Zones! "
            "This platform allows you to manage and monitor various zones within San Francisco effectively. "
            "Each zone can be assigned to team members, and its status can be updated in real-time. "
            "Feel free to explore the map and utilize the chat for any assistance."
        ),
        (
            "Assign zones to team members efficiently. "
            "Use the sidebar to select a zone, update its status, and assign it to the appropriate team member. "
            "This ensures that each area is managed properly and responsibilities are clearly defined. "
            "Efficient assignment helps in maintaining organized and effective operations."
        ),
        (
            "Monitor the status of each zone in real-time. "
            "Stay updated with the latest changes and progress within each neighborhood zone. "
            "Real-time monitoring enables prompt responses to any developments or issues that may arise. "
            "Keep track of all activities to ensure smooth and coordinated efforts."
        ),
        (
            "Need help? Use the chat on the right. "
            "Our integrated chat module allows you to communicate seamlessly with your team members. "
            "Whether you have questions, need assistance, or want to share updates, the chat is here for you. "
            "Effective communication is key to successful zone management."
        ),
        (
            "Stay updated with the latest zone activities. "
            "Receive notifications and updates about any significant changes or events in each zone. "
            "Staying informed helps in making informed decisions and taking timely actions. "
            "Regular updates ensure that everyone is on the same page and aware of ongoing activities."
        )
    ]

    # Custom CSS for the scrollable container and message blocks
    scrollable_css = """
    <style>
    .scrollable-container {
        display: flex;
        overflow-x: auto;
        padding: 20px 0;
        background-color: #f0f2f6;
    }
    .message-block {
        flex: 0 0 auto;
        background-color: #ffffff;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        padding: 20px 25px;
        margin-right: 15px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.15);
        min-width: 300px;
        max-width: 350px;
        height: auto;
        box-sizing: border-box;
        font-size: 16px;
        line-height: 1.5;
        text-align: left;
    }
    /* Hide scrollbar for WebKit browsers */
    .scrollable-container::-webkit-scrollbar {
        display: none;
    }
    /* Hide scrollbar for IE, Edge and Firefox */
    .scrollable-container {
        -ms-overflow-style: none;  /* IE and Edge */
        scrollbar-width: none;  /* Firefox */
    }
    </style>
    """

    # Create the scrollable message blocks
    messages_html = "<div class='scrollable-container'>"
    for msg in messages:
        messages_html += f"<div class='message-block'>{msg}</div>"
    messages_html += "</div>"

    # Render the CSS and HTML
    st.markdown(scrollable_css + messages_html, unsafe_allow_html=True)

    # --------------------------------------------------------------------------------- #

    # Create columns for layout: Map (75%) and Chat (25%)
    map_col, chat_col = st.columns([3, 1], gap="medium")

    with map_col:
        # Sidebar controls
        st.sidebar.subheader("Assign Zones and Update Status")
        zone_names = [zone["name"] for zone in st.session_state["zones"]]
        zone_name = st.sidebar.selectbox("Select Zone", zone_names)
        status = st.sidebar.selectbox("Select Status", ["Available", "In Progress", "Searched"])
        assigned_to = st.sidebar.selectbox("Assign to", ["None"] + people)

        if st.sidebar.button("Update Zone"):
            # Determine assignment
            assignment = assigned_to if assigned_to != "None" else None
            # Update zones
            st.session_state["zones"] = update_zone(
                st.session_state["zones"], zone_name, status, assignment
            )

        # Create a placeholder for the map
        map_placeholder = st.empty()

        # Always render the map
        render_google_map(
            st.session_state["zones"],
            api_key=config.get("google_maps_api_key", ""),
            pins=[],
            map_placeholder=map_placeholder
        )

    with chat_col:
        # Create placeholders to control the layout
        # Messages will appear above the input form
        messages_placeholder = st.empty()
        input_placeholder = st.empty()

        # ---- Process User Input First ---- #
        # Handle form submission before rendering messages
        with input_placeholder:
            with st.form(key="chat_form", clear_on_submit=True):
                user_input = st.text_input("You:", key="user_input")
                submit_button = st.form_submit_button(label="Send")

            if submit_button and user_input.strip():
                # Pass user_input directly to handle_user_input
                handle_user_input(user_input)
                new_pins = [
                    {"latitude": 37.8024, "longitude": -122.4058, "label": "Coit Tower"},
                    {"latitude": 37.7694, "longitude": -122.4862, "label": "Golden Gate Park"},
                ]
                render_google_map(
                    st.session_state["zones"],
                    api_key=config.get("google_maps_api_key", ""),
                    pins=new_pins,
                    map_placeholder=map_placeholder
                )

        # ---- Display Chat Messages Below ---- #
        with messages_placeholder:
            display_chat()

        # **Note:** Since `messages_placeholder` is defined before `input_placeholder` in the code,
        # Streamlit will render `messages_placeholder` **above** `input_placeholder` in the UI,
        # while ensuring that user input is processed before messages are displayed.



if __name__ == "__main__":
    main()
