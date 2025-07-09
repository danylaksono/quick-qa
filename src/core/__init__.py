"""
Core functionality for the GeoData QA application.
"""

from .data_loader import load_data
from .qa_calculator import calculate_qa_stats
from .database import get_duckdb_connection

__all__ = ["load_data", "calculate_qa_stats", "get_duckdb_connection"] 