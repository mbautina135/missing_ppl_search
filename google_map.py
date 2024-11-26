import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.wkt import loads
from shapely.geometry import Polygon, MultiPolygon
import json


def prepare_data_from_polygons(file_path):  # Replace with your file path
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
            zones.append({"name": row['name'], "coordinates": coords, "status": "Available"})
    return zones

# Function to handle MultiPolygon and Polygon geometries
def extract_polygons(row):
    if isinstance(row['geometry'], MultiPolygon):
        # Iterate over individual polygons in MultiPolygon
        return [{'name': row['name'], 'geometry': poly} for poly in row['geometry'].geoms]
    elif isinstance(row['geometry'], Polygon):
        # Return single polygon
        return [{'name': row['name'], 'geometry': row['geometry']}]
    return []

def render_google_map(zones, api_key):
    """Render the Google Map with zones and boundary."""
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
              zoom: 13,
            }});

            // Render zones
            const zones = {zones_json};
            zones.forEach((zone) => {{
              const polygon = new google.maps.Polygon({{
                paths: zone.coordinates,
                strokeColor: "#000",
                strokeOpacity: 0.8,
                strokeWeight: 2,
                fillColor: getFillColor(zone.status),
                fillOpacity: 0.35,
                map: map,
              }});

              const infoWindow = new google.maps.InfoWindow({{
                content: `<strong>${{zone.name}}</strong><br>Status: ${{zone.status}}`,
              }});

              polygon.addListener("click", () => {{
                infoWindow.setPosition(getPolygonCenter(zone.coordinates));
                infoWindow.open(map);
              }});
            }});

            function getFillColor(status) {{
              switch (status) {{
                case "Available": return "#00FF00";
                case "In Progress": return "#FF0000";
                case "Searched": return "#0000FF";
                default: return "#FFFFFF";
              }}
            }}

            function getPolygonCenter(coordinates) {{
              let latSum = 0, lngSum = 0;
              coordinates.forEach(coord => {{
                latSum += coord.lat;
                lngSum += coord.lng;
              }});
              return {{
                lat: latSum / coordinates.length,
                lng: lngSum / coordinates.length
              }};
            }}
          }}
    </script>
    <script src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap" async defer></script>
    </body>
    </html>
    """

    st.components.v1.html(map_html, height=600)