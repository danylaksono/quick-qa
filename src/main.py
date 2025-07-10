"""
Main application entry point for the GeoData QA application.
"""

import logging
import streamlit as st

from .ui import (
    initialize_session_state,
    render_sidebar,
    render_home_tab,
    render_summary_tab,
    render_table_and_map_explorer_tab,
    render_chart_builder_tab,
    render_sql_query_tab,
    render_comparison_tab,
)
from .utils.constants import PAGE_CONFIG, SESSION_KEYS


def cleanup_on_startup() -> None:
    """Performs cleanup tasks on app startup."""
    # Clear any stale cache data
    try:
        st.cache_data.clear()
        st.cache_resource.clear()
        logging.info("Cache cleared on startup")
    except Exception as e:
        logging.warning(f"Could not clear cache on startup: {e}")


def main() -> None:
    """Main function to run the Streamlit app."""
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    # Perform startup cleanup
    cleanup_on_startup()
    
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()

    # Define tabs
    tab_names = ["🏠 Home"]
    if st.session_state.get(SESSION_KEYS["gdf1"]) is not None:
        tab_names.extend(
            [
                "📊 Summary & QA",
                "📊🗺️ Table & Map Explorer",
                "📈 Chart Builder",
                "🔎 SQL Query",
            ]
        )
    if st.session_state.get(SESSION_KEYS["gdf1"]) is not None and st.session_state.get(SESSION_KEYS["gdf2"]) is not None:
        tab_names.append("🆚 Compare Datasets")

    tabs = st.tabs(tab_names)
    
    # Conditional tab rendering
    with tabs[0]:
        render_home_tab()

    if "📊 Summary & QA" in tab_names:
        with tabs[tab_names.index("📊 Summary & QA")]:
            render_summary_tab(
                st.session_state[SESSION_KEYS["gdf1"]], 
                st.session_state[SESSION_KEYS["gdf1_name"]]
            )

    if "📊🗺️ Table & Map Explorer" in tab_names:
        with tabs[tab_names.index("📊🗺️ Table & Map Explorer")]:
            render_table_and_map_explorer_tab(st.session_state[SESSION_KEYS["gdf1"]])

    if "📈 Chart Builder" in tab_names:
        with tabs[tab_names.index("📈 Chart Builder")]:
            render_chart_builder_tab(st.session_state[SESSION_KEYS["gdf1"]])

    if "🔎 SQL Query" in tab_names:
        with tabs[tab_names.index("🔎 SQL Query")]:
            render_sql_query_tab(st.session_state[SESSION_KEYS["gdf1"]], "data1")

    if "🆚 Compare Datasets" in tab_names:
        with tabs[tab_names.index("🆚 Compare Datasets")]:
            render_comparison_tab(
                st.session_state[SESSION_KEYS["gdf1"]],
                st.session_state[SESSION_KEYS["gdf2"]],
                st.session_state[SESSION_KEYS["gdf1_name"]],
                st.session_state[SESSION_KEYS["gdf2_name"]],
            )


if __name__ == "__main__":
    main() 