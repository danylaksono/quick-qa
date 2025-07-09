"""
Type hints and aliases for the GeoData QA application.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

import duckdb
import geopandas as gpd
import pandas as pd
import pydeck as pdk

# --- Type Hinting Aliases ---
GeoDataFrame = gpd.GeoDataFrame
DataFrame = pd.DataFrame
PydeckChart = pdk.Deck
AltairChart = Any  # Using Any for Altair to avoid dependency if not used everywhere
DuckDBCon = duckdb.DuckDBPyConnection

# Common type aliases
QAStats = Dict[str, Any]
FileUpload = Any  # Streamlit file uploader type 