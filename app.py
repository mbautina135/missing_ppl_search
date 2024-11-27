# app.py

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

    # Main title for the app
    st.title("San Francisco Mini Neighborhood Zones and Chat")

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
            st.success(f"Zone '{zone_name}' updated successfully.")

        # Create a placeholder for the map
        map_placeholder = st.empty()

        # Always render the map
        render_google_map(
            st.session_state["zones"],
            api_key=config.get("google_maps_api_key", ""),
            placeholder=map_placeholder
        )

    with chat_col:
        st.subheader("Chat Interface")

        # Display chat messages
        display_chat()

        # Input form for user messages
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_input("You:", key="user_input")
            submit_button = st.form_submit_button(label="Send")

        if submit_button and user_input.strip():
            # Pass user_input directly to handle_user_input
            handle_user_input(user_input)

if __name__ == "__main__":
    main()
