"""
Sidebar UI components for file uploads and session state management.
"""

import streamlit as st

from src.core.data_loader import load_data
from src.utils.constants import SESSION_KEYS, FILE_TYPES


def initialize_session_state() -> None:
    """Initialize session state keys to ensure they exist."""
    for key in SESSION_KEYS.values():
        if key not in st.session_state:
            st.session_state[key] = None


def render_sidebar() -> None:
    """Renders the sidebar for file uploads."""
    with st.sidebar:
        st.image(
            "https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.svg",
            width=200,
        )
        st.title("GeoData QA Inspector")
        st.markdown(
            "Upload one or two geospatial files to inspect, visualize, and compare."
        )

        st.header("Primary Dataset")
        uploaded_file_1 = st.file_uploader(
            "Upload a GeoPackage or GeoParquet file",
            type=FILE_TYPES,
            key="primary_uploader",
        )

        if uploaded_file_1:
            st.session_state[SESSION_KEYS["gdf1"]] = load_data(uploaded_file_1, uploaded_file_1.name)
            st.session_state[SESSION_KEYS["gdf1_name"]] = uploaded_file_1.name

        st.header("Comparison Dataset (Optional)")
        uploaded_file_2 = st.file_uploader(
            "Upload a second file to enable comparison",
            type=FILE_TYPES,
            key="secondary_uploader",
        )

        if uploaded_file_2:
            st.session_state[SESSION_KEYS["gdf2"]] = load_data(uploaded_file_2, uploaded_file_2.name)
            st.session_state[SESSION_KEYS["gdf2_name"]] = uploaded_file_2.name
        
        st.info("Geodata QA Inspector - v.1.0.0 2025") 