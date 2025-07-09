"""
Constants and configuration values for the GeoData QA application.
"""

import streamlit as st

# --- Streamlit Configuration ---
PAGE_CONFIG = {
    "page_title": "GeoData QA Inspector",
    "page_icon": "🔎",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# --- Session State Keys ---
SESSION_KEYS = {
    "gdf1": "gdf1",
    "gdf2": "gdf2",
    "gdf1_name": "gdf1_name",
    "gdf2_name": "gdf2_name",
}

# --- File Upload Configuration ---
SUPPORTED_FORMATS = ["gpkg", "parquet"]
FILE_TYPES = ["gpkg", "parquet"]

# --- Map Configuration ---
BASEMAP_OPTIONS = ["light", "dark", "satellite", "road"]
DEFAULT_BASEMAP = "road"

# --- Chart Configuration ---
CHART_TYPES = ["Histogram (Numeric)", "Bar Chart (Categorical)"]
HISTOGRAM_BINS_RANGE = (5, 100, 20)

# --- Color Palette for Categorical Data ---
BASE_COLORS = [
    [255, 0, 0],    # Red
    [0, 255, 0],    # Green
    [0, 0, 255],    # Blue
    [255, 255, 0],  # Yellow
    [255, 0, 255],  # Magenta
    [0, 255, 255],  # Cyan
    [255, 128, 0],  # Orange
    [128, 0, 255],  # Purple
    [0, 128, 255],  # Light Blue
    [255, 0, 128],  # Pink
]

# --- Default Values ---
DEFAULT_COLOR = "#00A4FF"
DEFAULT_OPACITY = 0.8
DEFAULT_LINE_WIDTH = 10 