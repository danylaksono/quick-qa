"""
Database connection and operations for the GeoData QA application.
"""

import duckdb
import streamlit as st

from src.utils.types import DuckDBCon


@st.cache_resource
def get_duckdb_connection() -> DuckDBCon:
    """Creates and returns a DuckDB connection."""
    return duckdb.connect(database=":memory:", read_only=False) 