import json
import geopandas as gpd
import streamlit as st
from shapely.geometry import Polygon, MultiPolygon, MultiPoint, Point
from shapely.ops import voronoi_diagram
import random
import streamlit.components.v1 as components
from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel

# Load the GeoJSON boundary file
geojson_path = "san_francisco_cleaned_boundary.geojson"  # Replace with your GeoJSON file path
boundary_gdf = gpd.read_file(geojson_path)

# Combine all geometries into one if necessary
boundary_polygon = boundary_gdf.geometry.unary_union

# Function to generate random points inside the boundary
def generate_random_points(boundary, num_points):
    points = []
    minx, miny, maxx, maxy = boundary.bounds
    while len(points) < num_points:
        random_point = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if boundary.contains(random_point):
            points.append(random_point)
    return points

# Function to generate Voronoi polygons
def generate_voronoi_polygons(boundary, num_points):
    points = generate_random_points(boundary, num_points)
    multipoint = MultiPoint(points)
    voronoi = voronoi_diagram(multipoint, envelope=boundary.envelope)

    clipped_polygons = []
    for polygon in voronoi.geoms:
        intersection = polygon.intersection(boundary)
        if not intersection.is_empty:
            clipped_polygons.append(intersection)

    return gpd.GeoDataFrame(geometry=clipped_polygons, crs="EPSG:4326")

# Generate Voronoi polygons
num_points = 150  # Adjust as needed for density
mini_neighborhoods_gdf = generate_voronoi_polygons(boundary_polygon, num_points)

# Convert Voronoi polygons to JSON
zones = []
for i, row in mini_neighborhoods_gdf.iterrows():
    if isinstance(row.geometry, Polygon):  # Handle individual polygons
        coords = [{"lat": coord[1], "lng": coord[0]} for coord in row.geometry.exterior.coords]
        zones.append({"name": f"Zone {i + 1}", "coordinates": coords, "status": "Available"})
    elif isinstance(row.geometry, MultiPolygon):  # Handle MultiPolygon
        for poly in row.geometry.geoms:
            coords = [{"lat": coord[1], "lng": coord[0]} for coord in poly.exterior.coords]
            zones.append({"name": f"Zone {i + 1}", "coordinates": coords, "status": "Available"})

# Store zones in session state
if "zones" not in st.session_state:
    st.session_state["zones"] = zones

# Sidebar for chat
st.sidebar.title("Volunteer Chat with Google Gemini (via Vertex AI)")
st.sidebar.markdown("Use this chat to communicate with Google Gemini for questions and updates.")

# Initialize session state for chat messages
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_user_input" not in st.session_state:
    st.session_state.last_user_input = ""

# CSS to fix layout and scrolling
st.sidebar.markdown(
    """
    <style>
        /* Remove unnecessary padding/margin from the sidebar */
        .css-1d391kg, .css-1kyxreq {
            padding: 0 !important;
            margin: 0 !important;
        }

        /* Scrollable chat container */
        .scrollable-chat {
            max-height: 300px; /* Limit max height to avoid overflowing */
            overflow-y: auto;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 5px;
            background-color: #f9f9f9;
        }

        /* Chat message styling */
        .chat-message {
            margin-bottom: 10px;
            font-size: 14px;
        }

        .chat-user {
            color: #1a73e8;
            font-weight: bold;
        }

        .chat-assistant {
            color: #34a853;
            font-weight: bold;
        }

        /* Adjust chat input alignment */
        .chat-input {
            margin-top: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Display chat messages in a scrollable container
st.sidebar.markdown('<div class="scrollable-chat">', unsafe_allow_html=True)

if st.session_state.messages:
    for message in st.session_state.messages:
        role_icon = "🤖" if message["role"] == "assistant" else "🙂"
        st.sidebar.markdown(
            f'<div class="chat-message"><strong>{role_icon} {message["role"].capitalize()}:</strong> {message["content"]}</div>',
            unsafe_allow_html=True,
        )
else:
    st.sidebar.markdown('<div class="chat-message">No messages yet...</div>', unsafe_allow_html=True)

st.sidebar.markdown("</div>", unsafe_allow_html=True)

# Chat input in the sidebar
user_input = st.sidebar.text_input(
    "Type your message...",
    key="chat_input",
    placeholder="Enter a message",
    label_visibility="collapsed",
)

if user_input != st.session_state.last_user_input and user_input.strip():
    # Add user's message
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.last_user_input = user_input

    # Call Gemini for a response
    try:
        # Initialize Vertex AI client
        def initialize_vertex_ai(project_id, region="us-central1"):
            aiplatform.init(project=project_id, location=region)

        # Chat with Gemini using Vertex AI
        def ask_gemini(prompt):
            gemini_model = GenerativeModel('gemini-pro-vision')
            model_response = gemini_model.generate_content([prompt])
            return model_response.text

        # GCP Project ID
        PROJECT_ID = "gcp103037-gcpenvironment"  # Replace with your GCP Project ID
        initialize_vertex_ai(PROJECT_ID)
        GOOGLE_APPLICATION_CREDENTIALS = "/Users/npoly/Downloads/gcp103037-gcpenvironment-086f79e83506.json"

        # Send the user's message to Gemini
        response = ask_gemini(user_input)
        st.session_state.messages.append({"role": "assistant", "content": response})
    except Exception as e:
        st.session_state.messages.append({"role": "assistant", "content": f"Error: {str(e)}"})

# Task assignment in the sidebar
st.sidebar.title("Assign Tasks")
if st.session_state["zones"]:
    selected_zone = st.sidebar.selectbox("Select a Zone", [zone["name"] for zone in st.session_state["zones"]])
    selected_status = st.sidebar.selectbox("Select Status", ["Available", "In Progress", "Searched"])

    if st.sidebar.button("Update Zone Status"):
        for zone in st.session_state["zones"]:
            if zone["name"] == selected_zone:
                zone["status"] = selected_status
                st.sidebar.success(f"{selected_zone} updated to '{selected_status}'!")

# Google Maps integration
boundary_json = json.dumps([
    [{"lat": coord[1], "lng": coord[0]} for coord in boundary_polygon.exterior.coords]
] if isinstance(boundary_polygon, Polygon) else [
    [{"lat": coord[1], "lng": coord[0]} for coord in poly.exterior.coords]
    for poly in boundary_polygon.geoms
])

zones_json = json.dumps(st.session_state["zones"])
API_KEY = "AIzaSyD968rGaVguoUXU-nQZmAr9t9UNPzngEUw"  # Replace with your actual API key
map_html = f"""
<!DOCTYPE html>
<html>
  <head>
    <style>
      #map {{
        height: 600px;
        width: 100%;
      }}
    </style>
  </head>
  <body>
    <div id="map"></div>
    <script>
      function initMap() {{
        const map = new google.maps.Map(document.getElementById("map"), {{
          center: {{ lat: 37.7749, lng: -122.4194 }},
          zoom: 13,
        }});

        // Render boundary
        const boundary = {boundary_json};
        boundary.forEach(coords => {{
          const boundaryPolygon = new google.maps.Polygon({{
            paths: coords,
            strokeColor: "#FF0000",
            strokeOpacity: 0.8,
            strokeWeight: 2,
            fillColor: "#FF0000",
            fillOpacity: 0.1,
          }});
          boundaryPolygon.setMap(map);
        }});

        // Render zones
        const zones = {zones_json};
        zones.forEach(zone => {{
          const polygon = new google.maps.Polygon({{
            paths: zone.coordinates,
            strokeColor: "#0000FF",
            strokeOpacity: 0.8,
            strokeWeight: 2,
            fillColor: "#00FF00",
            fillOpacity: 0.35,
          }});
          polygon.setMap(map);
        }});
      }}
    </script>
    <script async defer src="https://maps.googleapis.com/maps/api/js?key={API_KEY}&callback=initMap"></script>
  </body>
</html>
"""

# Main map display
st.title("San Francisco Mini Neighborhood Zones")
st.markdown("Explore the zones and their statuses on the map below:")
st.components.v1.html(map_html, height=600)
