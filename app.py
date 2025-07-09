# GeoData QA App - Modular Version
#
# This script creates a Streamlit application for Quality Assurance of geospatial data.
# It allows users to upload, inspect, visualize, and compare geospatial datasets.
#
# Author: Dany Laksono
# Date: July 3, 2025

import streamlit as st

from src.main import main
from src.utils.constants import PAGE_CONFIG

# --- Configuration ---
st.set_page_config(**PAGE_CONFIG)

# Run the main application
if __name__ == "__main__":
    main() 