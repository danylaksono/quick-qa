"""
Sidebar UI components for file uploads and session state management.
"""

import streamlit as st

from src.core.data_loader import load_data, clear_data_cache
from src.utils.constants import SESSION_KEYS, FILE_TYPES


def initialize_session_state() -> None:
    """Initialize session state keys to ensure they exist."""
    for key in SESSION_KEYS.values():
        if key not in st.session_state:
            st.session_state[key] = None


def clear_data_and_cache() -> None:
    """Clears all data from session state and clears cache."""
    # Clear session state
    for key in SESSION_KEYS.values():
        st.session_state[key] = None
    
    # Clear Streamlit cache using the dedicated function
    clear_data_cache()
    
    # Show toast notification
    st.toast("🗑️ All data cleared", icon="🗑️")
    
    # Force rerun to update UI
    st.rerun()


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

        # Track previous state to detect changes
        if "prev_uploaded_file_1" not in st.session_state:
            st.session_state.prev_uploaded_file_1 = None

        if uploaded_file_1:
            if st.session_state.prev_uploaded_file_1 != uploaded_file_1.name:
                st.session_state[SESSION_KEYS["gdf1"]] = load_data(uploaded_file_1, uploaded_file_1.name)
                st.session_state[SESSION_KEYS["gdf1_name"]] = uploaded_file_1.name
                st.session_state.prev_uploaded_file_1 = uploaded_file_1.name
                st.toast(f"✅ Loaded: {uploaded_file_1.name}", icon="📁")
        else:
            # File was removed - clear the data
            if st.session_state.prev_uploaded_file_1 is not None:
                st.session_state[SESSION_KEYS["gdf1"]] = None
                st.session_state[SESSION_KEYS["gdf1_name"]] = None
                st.session_state.prev_uploaded_file_1 = None
                clear_data_cache()
                st.toast("🗑️ Primary dataset cleared", icon="🗑️")
                st.rerun()

        st.header("Comparison Dataset (Optional)")
        uploaded_file_2 = st.file_uploader(
            "Upload a second file to enable comparison",
            type=FILE_TYPES,
            key="secondary_uploader",
        )

        # Track previous state for secondary file
        if "prev_uploaded_file_2" not in st.session_state:
            st.session_state.prev_uploaded_file_2 = None

        if uploaded_file_2:
            if st.session_state.prev_uploaded_file_2 != uploaded_file_2.name:
                st.session_state[SESSION_KEYS["gdf2"]] = load_data(uploaded_file_2, uploaded_file_2.name)
                st.session_state[SESSION_KEYS["gdf2_name"]] = uploaded_file_2.name
                st.session_state.prev_uploaded_file_2 = uploaded_file_2.name
                st.toast(f"✅ Loaded: {uploaded_file_2.name}", icon="📁")
        else:
            # File was removed - clear the data
            if st.session_state.prev_uploaded_file_2 is not None:
                st.session_state[SESSION_KEYS["gdf2"]] = None
                st.session_state[SESSION_KEYS["gdf2_name"]] = None
                st.session_state.prev_uploaded_file_2 = None
                clear_data_cache()
                st.toast("🗑️ Comparison dataset cleared", icon="🗑️")
                st.rerun()
        
        st.info("Geodata QA Inspector - v.1.0.0 2025") 