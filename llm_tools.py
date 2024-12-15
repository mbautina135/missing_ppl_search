# llm_tools.py

from vertexai.generative_models import (
    FunctionDeclaration,
    Tool,
)
from map_operations import add_pin, update_zone
from updates_operations import update_volunteer_insights
import streamlit as st

# Function declaration for adding a pin to the map
add_pin_func = FunctionDeclaration(
    name="add_pin",
    description="Add a pin to the map with a specified location, label, and incident type.",
    parameters={
        "type": "object",
        "properties": {
            "lat": {
                "type": "number",
                "description": "The latitude of the pin's location."
            },
            "lon": {
                "type": "number",
                "description": "The longitude of the pin's location."
            },
            "label": {
                "type": "string",
                "description": "A descriptive label for the pin."
            },
            "incident_type": {
                "type": "string",
                "description": "The type of incident for the pin, either 'collision' or 'robbery'.",
                "enum": ["collision", "robbery"]
            }
        },
        "required": ["lat", "lon", "label", "incident_type"]
    }
)

# Function declaration for updating a zone's status
update_zone_func = FunctionDeclaration(
    name="update_zone",
    description="""Update the status of a specified zone and optionally assign it to a user. 
                   Updates are reflected on the map.
                   Available statuses are: 'Available', 'In Progress', 'Searched'.""",
    parameters={
        "type": "object",
        "properties": {
            "zone_name": {
                "type": "string",
                "description": "The name of the zone to update."
            },
            "status": {
                "type": "string",
                "description": "The new status to set for the zone.",
                "enum": ["Available", "In Progress", "Searched"]
            },
            "assigned_to": {
                "type": "string",
                "description": "The user assigned to the zone (optional)."
            }
        },
        "required": ["zone_name", "status"]
    }
)

update_volunteer_insights_func = FunctionDeclaration(
    name="update_volunteer_insights",
    description="""Add a new volunteer update to the insights file stored in Google Cloud Storage (GCS). 
                   Each update includes details about the location, description. 
                   Automatically generates an Update_ID, timestamps the entry, and assigns 'Nataliya' as the default volunteer.""",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The location reported in the update."
            },
            "details": {
                "type": "string",
                "description": "A description or details of the update."
            }
        },
        "required": ["location", "details"]
    }
)


# Tools available to the LLM
tools = Tool([add_pin_func, update_zone_func, update_volunteer_insights_func])

def get_functions():
    """
    Returns a dictionary mapping function names to their implementations.
    """
    return {
        "add_pin": add_pin,
        "update_volunteer_insights": update_volunteer_insights,
        "update_zone": lambda zone_name, status, assigned_to=None: update_zone(
            st.session_state["zones"], zone_name, status, assigned_to
        ),
    }
