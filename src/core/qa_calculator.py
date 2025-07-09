"""
Quality Assurance calculations for geospatial data.
"""

import logging
from typing import Dict, Any

import geopandas as gpd
import pandas as pd
import streamlit as st

from src.utils.types import GeoDataFrame, QAStats


@st.cache_data(show_spinner="Calculating QA stats...")
def calculate_qa_stats(_gdf: GeoDataFrame) -> QAStats:
    """
    Calculates various quality assurance statistics for a GeoDataFrame.

    Args:
        _gdf: The input GeoDataFrame.

    Returns:
        A dictionary containing QA metrics.
    """
    stats = {}
    try:
        # Basic Info
        stats["rows"], stats["cols"] = _gdf.shape
        stats["crs"] = _gdf.crs.to_string() if _gdf.crs else "Not Defined"
        stats["memory"] = f"{_gdf.memory_usage(deep=True).sum() / 1e6:.2f} MB"

        # Missing Values
        missing = _gdf.isnull().sum()
        stats["missing_values"] = missing[missing > 0].sort_values(ascending=False)

        # Constant Columns
        nunique = _gdf.nunique()
        # Fix the index access issue by using a different approach
        constant_cols = []
        for col in _gdf.columns:
            if _gdf[col].nunique() == 1:
                constant_cols.append(col)
        stats["constant_columns"] = constant_cols

        # Geometry Stats
        if "geometry" in _gdf.columns and not _gdf.geometry.empty:
            stats["geom_types"] = _gdf.geometry.geom_type.value_counts()
            stats["empty_geoms"] = _gdf.geometry.is_empty.sum()
            stats["invalid_geoms"] = (~_gdf.geometry.is_valid).sum()
            stats["bbox"] = _gdf.total_bounds
        else:
            stats["geom_types"] = pd.Series(dtype=int)
            stats["empty_geoms"] = 0
            stats["invalid_geoms"] = 0
            stats["bbox"] = None

    except Exception as e:
        st.error(f"An error occurred during QA calculation: {e}")
        logging.error(f"QA calculation failed: {e}")
        return {}

    return stats 