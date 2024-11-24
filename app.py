import json
import streamlit as st
from chat_module import initialize_chat_session, display_chat, handle_user_input
from google_map import (
    load_boundary, generate_voronoi_polygons, prepare_zones, render_google_map
)

# Load config.json
with open("config.json") as config_file:
    config = json.load(config_file)

# Page configuration
st.set_page_config(
    page_title="Map and Chat",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Pre-generate the map
geojson_path = config["geojson_path"]
num_points = 150  # Fixed number of points for Voronoi polygons
boundary_polygon = load_boundary(geojson_path)
mini_neighborhoods_gdf = generate_voronoi_polygons(boundary_polygon, num_points)
zones = prepare_zones(mini_neighborhoods_gdf)

# Store zones and boundary in session state
if "zones" not in st.session_state:
    st.session_state["zones"] = zones
if "boundary_polygon" not in st.session_state:
    st.session_state["boundary_polygon"] = boundary_polygon

# Initialize chat session
initialize_chat_session()

# Main title for the app
st.title("San Francisco Mini Neighborhood Zones and Chat")

# Main layout with two columns: Map on the left, Chat on the right
col1, col2 = st.columns([3, 2])  # Adjust proportions as needed (e.g., [2, 1])

# Left column: Google Map
with col1:
    render_google_map(
        st.session_state["boundary_polygon"],
        st.session_state["zones"],
        api_key=config["google_maps_api_key"],
    )

# Right column: Chat Interface
with col2:
    display_chat()
    st.text_input(
        "Type your message",
        key="user_input",
        placeholder="Type a message and press Enter",
        on_change=handle_user_input,
    )
