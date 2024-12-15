# config.py

import json
import os
from google.oauth2 import service_account
from google.cloud import aiplatform
import streamlit as st

def load_config(config_path="config/config.json"):
    """
    Load configuration from a JSON file.
    """
    try:
        with open(config_path) as config_file:
            config = json.load(config_file)
        return config
    except FileNotFoundError:
        st.error("Configuration file 'config.json' not found.")
        return None
    except json.JSONDecodeError:
        st.error("Error decoding 'config.json'. Please check the file format.")
        return None

def initialize_credentials(config):
    """
    Initialize Google Cloud credentials and AI Platform.
    """
    service_account_path = config.get("service_account_path", "")
    if not service_account_path:
        st.error("Service account path not provided in configuration.")
        return False

    if not os.path.exists(service_account_path):
        st.error(f"Service account file '{service_account_path}' does not exist.")
        return False

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path
    try:
        credentials = service_account.Credentials.from_service_account_file(service_account_path)
        aiplatform.init(credentials=credentials)
    except Exception as e:
        st.error(f"Failed to initialize AI Platform: {e}")
        return False

    st.session_state["api_key"] = config.get("google_maps_api_key", "")
    st.session_state["config"] = config
    return True
