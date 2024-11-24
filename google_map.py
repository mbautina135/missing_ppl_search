import json
import random
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, Point, MultiPoint
from shapely.ops import voronoi_diagram
import streamlit as st

def load_boundary(geojson_path):
    """Load GeoJSON boundary file and return a unified boundary polygon."""
    boundary_gdf = gpd.read_file(geojson_path)
    return boundary_gdf.geometry.unary_union

def generate_random_points(boundary, num_points):
    """Generate random points inside the boundary polygon."""
    points = []
    minx, miny, maxx, maxy = boundary.bounds
    while len(points) < num_points:
        random_point = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if boundary.contains(random_point):
            points.append(random_point)
    return points

def generate_voronoi_polygons(boundary, num_points):
    """Generate Voronoi polygons clipped to the boundary."""
    points = generate_random_points(boundary, num_points)
    multipoint = MultiPoint(points)
    voronoi = voronoi_diagram(multipoint, envelope=boundary.envelope)

    clipped_polygons = [
        polygon.intersection(boundary)
        for polygon in voronoi.geoms
        if not polygon.intersection(boundary).is_empty
    ]
    return gpd.GeoDataFrame(geometry=clipped_polygons, crs="EPSG:4326")

def prepare_zones(mini_neighborhoods_gdf):
    """Convert Voronoi polygons to JSON format for rendering."""
    zones = []
    for i, row in mini_neighborhoods_gdf.iterrows():
        if isinstance(row.geometry, Polygon):
            coords = [{"lat": coord[1], "lng": coord[0]} for coord in row.geometry.exterior.coords]
            zones.append({"name": f"Zone {i + 1}", "coordinates": coords, "status": "Available"})
        elif isinstance(row.geometry, MultiPolygon):
            for poly in row.geometry.geoms:
                coords = [{"lat": coord[1], "lng": coord[0]} for coord in poly.exterior.coords]
                zones.append({"name": f"Zone {i + 1}", "coordinates": coords, "status": "Available"})
    return zones

def render_google_map(boundary_polygon, zones, api_key):
    """Render the Google Map with zones and boundary."""
    boundary_json = json.dumps([
        [{"lat": coord[1], "lng": coord[0]} for coord in boundary_polygon.exterior.coords]
    ] if isinstance(boundary_polygon, Polygon) else [
        [{"lat": coord[1], "lng": coord[0]} for coord in poly.exterior.coords]
        for poly in boundary_polygon.geoms
    ])
    zones_json = json.dumps(zones)

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
        <script async defer src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap"></script>
      </body>
    </html>
    """
    st.components.v1.html(map_html, height=600)
