# google_map.py

import json
import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.wkt import loads
from shapely.geometry import Polygon, MultiPolygon

def prepare_data_from_polygons(file_path):
    """
    Prepare zone data from a CSV file containing polygon geometries in WKT format.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        list: A list of zones with their names, coordinates, status, and assignment.
    """
    sf_districts_data = pd.read_csv(file_path)

    # Parse WKT geometries
    sf_districts_data['geometry'] = sf_districts_data['the_geom'].apply(lambda x: loads(x) if x else None)
    
    # Expand MultiPolygons into individual polygons
    expanded_rows = []
    for _, row in sf_districts_data.iterrows():
        expanded_rows.extend(extract_polygons(row))

    # Create a GeoDataFrame with cleaned geometries
    cleaned_gdf = gpd.GeoDataFrame(expanded_rows, crs="EPSG:4326")

    # Convert geometries to JSON-like structures for Google Maps
    zones = []
    for _, row in cleaned_gdf.iterrows():
        if isinstance(row['geometry'], Polygon):
            coords = [{"lat": coord[1], "lng": coord[0]} for coord in row['geometry'].exterior.coords]
            zones.append({
                "name": row['name'],
                "coordinates": coords,
                "status": "Available",
                "assigned_to": None
            })
    return zones

def extract_polygons(row):
    """
    Extract individual polygons from a row that may contain MultiPolygon or Polygon geometries.

    Args:
        row (pd.Series): A row from the GeoDataFrame.

    Returns:
        list: A list of dictionaries with zone names and geometries.
    """
    if isinstance(row['geometry'], MultiPolygon):
        # Iterate over individual polygons in MultiPolygon
        return [{'name': row['name'], 'geometry': poly} for poly in row['geometry'].geoms]
    elif isinstance(row['geometry'], Polygon):
        # Return single polygon
        return [{'name': row['name'], 'geometry': row['geometry']}]
    return []

def render_google_map(zones, api_key, placeholder):
    """
    Render the Google Map with zones and interactivity within a Streamlit placeholder.

    Args:
        zones (list): List of zone dictionaries.
        api_key (str): Google Maps API key.
        placeholder (streamlit.delta_generator.DeltaGenerator): Streamlit placeholder to render the map.
    """
    zones_json = json.dumps(zones)

    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
          #map {{
            height: 100%;
            width: 100%;
          }}
          html, body {{
            height: 100%;
            margin: 0;
            padding: 0;
          }}
    </style>
    </head>
    <body>
    <div id="map"></div>
    <script>
          function initMap() {{
            const map = new google.maps.Map(document.getElementById("map"), {{
              center: {{ lat: 37.7749, lng: -122.4194 }},
              zoom: 12,  // Adjusted zoom level for a zoomed-out view
            }});

            // Render zones
            const zones = {zones_json};
            const polygons = [];

            // Initialize a single InfoWindow instance
            const infoWindow = new google.maps.InfoWindow();

            zones.forEach((zone, index) => {{
              const polygon = new google.maps.Polygon({{
                paths: zone.coordinates,
                strokeColor: "#000",
                strokeOpacity: 0.8,
                strokeWeight: 2,
                fillColor: getFillColor(zone.status),
                fillOpacity: 0.35,
                map: map,
              }});

              polygons.push({{ polygon: polygon, zone: zone }});

              polygon.addListener("click", (event) => {{
                // Set the content and position of the single InfoWindow
                const contentString = `<strong>${{zone.name}}</strong><br>Status: ${{zone.status}}<br>Assigned to: ${{zone.assigned_to || "None"}}`;
                infoWindow.setContent(contentString);
                infoWindow.setPosition(event.latLng);
                infoWindow.open(map);
              }});
            }});

            function getFillColor(status) {{
              switch (status) {{
                case "Available": return "#00FF00";
                case "In Progress": return "#FFFF00";
                case "Searched": return "#FF0000";
                default: return "#FFFFFF";
              }}
            }}

            // Add click listener to the map for preview info window
            map.addListener("click", (mapsMouseEvent) => {{
              const clickedLatLng = mapsMouseEvent.latLng;
              let foundZone = null;

              for (let i = 0; i < polygons.length; i++) {{
                const poly = polygons[i].polygon;
                const zone = polygons[i].zone;
                if (google.maps.geometry.poly.containsLocation(clickedLatLng, poly)) {{
                  foundZone = zone;
                  break;
                }}
              }}

              if (foundZone) {{
                const previewInfoWindow = new google.maps.InfoWindow({{
                  content: `<div><strong>${{foundZone.name}}</strong></div>`,
                  position: clickedLatLng,
                  pixelOffset: new google.maps.Size(0, -30)
                }});
                previewInfoWindow.open(map);
                
                // Optional: Close the preview after a short delay
                setTimeout(() => {{
                  previewInfoWindow.close();
                }}, 3000); // Closes after 3 seconds
              }}
            }});
          }}
    </script>
    <script src="https://maps.googleapis.com/maps/api/js?key={api_key}&libraries=geometry&callback=initMap" async defer></script>
    </body>
    </html>
    """

    with placeholder:
        st.components.v1.html(map_html, height=600)
