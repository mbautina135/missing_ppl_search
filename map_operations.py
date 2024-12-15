import streamlit as st
from google_map import render_google_map

def add_pin(lat, lon, label, incident_type):
    icons = {
        'collision': 'https://raw.githubusercontent.com/NataliaPolyakovska/icons/main/crash.png',
        'robbery': 'https://raw.githubusercontent.com/NataliaPolyakovska/icons/main/thief.png',
        'other danger': 'https://raw.githubusercontent.com/NataliaPolyakovska/icons/main/warning.png',
        'belongings': 'https://raw.githubusercontent.com/NataliaPolyakovska/icons/main/sack.png',
    }
    st.session_state['pins'].append({
        "latitude": lat,
        "longitude": lon,
        "label": label,
        "icon": icons[incident_type]
    })
    return True 

def update_zone(zones, zone_name, status, assigned_to=None):
    for zone in zones:
        if zone["name"] == zone_name:
            zone["status"] = status
            if assigned_to:
                zone["assigned_to"] = assigned_to
    return True  
