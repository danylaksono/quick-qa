"""
Data loading functionality for geospatial files.
"""

import io
import logging
from typing import Optional

import geopandas as gpd
import pandas as pd
import streamlit as st

# Import shapely for geometry parsing
try:
    from shapely import wkb, wkt
    from shapely.errors import ShapelyError
except ImportError:
    # Shapely might not be available, but we'll handle this gracefully
    pass

# Import duckdb for better parquet handling
try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False

from src.utils.types import GeoDataFrame, FileUpload


@st.cache_data(show_spinner="Loading data...")
def load_data(uploaded_file: FileUpload, file_name: str) -> Optional[GeoDataFrame]:
    """
    Loads a geospatial file into a GeoDataFrame.
    
    Args:
        uploaded_file: The uploaded file object from Streamlit
        file_name: Name of the uploaded file
        
    Returns:
        GeoDataFrame if successful, None otherwise
    """
    if uploaded_file is None:
        return None
        
    try:
        if file_name.lower().endswith(".gpkg"):
            gdf = gpd.read_file(uploaded_file)
        elif file_name.lower().endswith((".parquet", ".geoparquet")):
            uploaded_file.seek(0)
            
            # Try DuckDB first for better parquet handling
            if DUCKDB_AVAILABLE:
                try:
                    # Write uploaded file to temporary location for DuckDB
                    import tempfile
                    import os
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.parquet') as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        tmp_file_path = tmp_file.name
                    
                    try:
                        # Use DuckDB to read and convert geometry
                        conn = duckdb.connect()
                        
                        # Install and load spatial extension
                        conn.execute("INSTALL spatial;")
                        conn.execute("LOAD spatial;")
                        
                        # Read parquet file
                        result = conn.execute(f"SELECT * FROM read_parquet('{tmp_file_path}')").fetchdf()
                        
                        # Find geometry column using our detection function
                        geom_cols = detect_geometry_columns(result)
                        
                        if geom_cols:
                            geom_col = geom_cols[0]
                            
                            # Try to convert geometry using DuckDB spatial functions
                            try:
                                # First try ST_GeomFromWKB if it's binary
                                geom_query = f"SELECT *, ST_AsText(ST_GeomFromWKB({geom_col})) as geometry_wkt FROM read_parquet('{tmp_file_path}')"
                                result_with_geom = conn.execute(geom_query).fetchdf()
                                
                                # Convert WKT to shapely geometries
                                geometries = safe_geometry_conversion(result_with_geom['geometry_wkt'], 'geometry_wkt')
                                
                                # Create GeoDataFrame
                                df_clean = result.drop(columns=[geom_col])
                                df_clean['geometry'] = geometries
                                gdf = gpd.GeoDataFrame(df_clean, geometry='geometry')
                                
                            except Exception:
                                # Fallback to manual parsing
                                geometries = safe_geometry_conversion(result[geom_col], geom_col)
                                df_clean = result.drop(columns=[geom_col])
                                df_clean['geometry'] = geometries
                                gdf = gpd.GeoDataFrame(df_clean, geometry='geometry')
                        else:
                            # No geometry column found
                            gdf = gpd.GeoDataFrame(result)
                            
                    finally:
                        # Clean up temporary file
                        os.unlink(tmp_file_path)
                        conn.close()
                        
                except Exception as e:
                    st.warning(f"DuckDB parsing failed: {e}. Falling back to pandas.")
                    uploaded_file.seek(0)
                    gdf = _load_parquet_pandas(uploaded_file)
            else:
                # Fallback to pandas if DuckDB not available
                gdf = _load_parquet_pandas(uploaded_file)
        else:
            st.error(
                "Unsupported file format. Please upload a GeoPackage (.gpkg) "
                "or GeoParquet (.parquet) file."
            )
            return None
            
        # Ensure a geometry column exists and has the correct name
        if "geometry" not in gdf.columns:
            st.warning(
                f"File '{file_name}' loaded, but no 'geometry' column was found. "
                "Mapping functionality will be disabled."
            )
        else:
            if gdf.geometry.name != "geometry":
                gdf = gdf.rename_geometry("geometry")
                
        return gdf
        
    except Exception as e:
        st.error(f"Error loading file '{file_name}': {e}")
        logging.error(f"Failed to load {file_name}: {e}")
        return None


def _load_parquet_pandas(uploaded_file):
    """Fallback function to load parquet using pandas."""
    df = pd.read_parquet(uploaded_file, engine='pyarrow')
    
    # Find geometry columns using our detection function
    geom_cols = detect_geometry_columns(df)
    
    if not geom_cols:
        # No geometry column found, return as regular GeoDataFrame
        return gpd.GeoDataFrame(df)
    
    geom_col = geom_cols[0]
    return _parse_geometry_fallback(df, geom_col)


def _parse_geometry_fallback(df, geom_col):
    """Parse geometry column using various fallback methods."""
    geom_series = df[geom_col]
    
    # Defensive geometry parsing
    try:
        # Try GeoDataFrame constructor (may work if already parsed)
        gdf = gpd.GeoDataFrame(df, geometry=geom_col)
        if not gdf.geometry.isna().all() and not gdf.geometry.empty:
            return gdf
    except Exception:
        pass
    
    # Use our safe geometry conversion
    geometries = safe_geometry_conversion(geom_series, geom_col)
    df_clean = df.drop(columns=[geom_col])
    df_clean['geometry'] = geometries
    gdf = gpd.GeoDataFrame(df_clean, geometry='geometry')
    
    return gdf


def safe_geometry_conversion(series, column_name: str):
    """
    Safely convert a pandas series to shapely geometries with comprehensive error handling.
    
    Args:
        series: pandas Series that might contain geometry data
        column_name: name of the column for error reporting
        
    Returns:
        pandas Series with shapely geometries or None values
    """
    import pandas as pd
    
    if series.empty:
        return series
    
    try:
        # Try direct conversion first (if already shapely objects)
        if hasattr(series.iloc[0], 'wkt'):
            return series
            
        # Try WKB conversion for binary data
        if series.dtype == 'object':
            first_val = series.dropna().iloc[0] if not series.dropna().empty else None
            
            if isinstance(first_val, (bytes, memoryview)):
                try:
                    return series.apply(lambda x: wkb.loads(x) if pd.notna(x) else None)
                except Exception:
                    try:
                        return series.apply(lambda x: wkb.loads(bytes(x)) if pd.notna(x) else None)
                    except Exception:
                        pass
            
            # Try WKT conversion for string data
            elif isinstance(first_val, str):
                try:
                    return series.apply(lambda x: wkt.loads(x) if pd.notna(x) else None)
                except Exception:
                    pass
                    
    except Exception as e:
        logging.warning(f"Geometry conversion failed for column '{column_name}': {e}")
    
    # If all else fails, return None series
    st.warning(f"Could not parse geometry column '{column_name}'. Geometries will be set to None.")
    return pd.Series([None] * len(series), index=series.index)


def prepare_dataframe_for_display(gdf: GeoDataFrame, max_rows: Optional[int] = None) -> pd.DataFrame:
    """
    Prepare a GeoDataFrame for display in Streamlit by converting geometry to WKT strings.
    
    Args:
        gdf: GeoDataFrame to prepare
        max_rows: Maximum number of rows to include (None for all rows)
        
    Returns:
        Regular DataFrame safe for Streamlit display
    """
    if gdf is None or gdf.empty:
        return pd.DataFrame()
    
    # Create a copy and limit rows if specified
    display_df = gdf.head(max_rows) if max_rows else gdf.copy()
    
    # Convert to regular pandas DataFrame first to avoid geometry dtype issues
    if hasattr(display_df, 'geometry') and "geometry" in display_df.columns:
        try:
            # Convert geometry to WKT with truncation for display
            geometry_wkt = display_df["geometry"].apply(
                lambda geom: geom.wkt[:100] + "..." if geom is not None and hasattr(geom, 'wkt') and len(geom.wkt) > 100
                else geom.wkt if geom is not None and hasattr(geom, 'wkt')
                else str(geom) if geom is not None 
                else None
            )
            
            # Create a new regular DataFrame with converted geometry
            columns_data = {}
            for col in display_df.columns:
                if col == 'geometry':
                    columns_data[col] = geometry_wkt
                else:
                    columns_data[col] = display_df[col].values
            
            # Create pure pandas DataFrame
            result_df = pd.DataFrame(columns_data, index=display_df.index)
            
            # Additional safety check: ensure no geometry objects remain
            for col in result_df.columns:
                if result_df[col].dtype == 'object':
                    # Check if any values are geometry objects
                    sample_values = result_df[col].dropna().head(5)
                    if any(hasattr(val, 'wkt') for val in sample_values if val is not None):
                        # Convert to string representation
                        result_df[col] = result_df[col].astype(str)
            
            return result_df
            
        except Exception as e:
            # If conversion fails, drop geometry column for display
            logging.warning(f"Could not convert geometry to WKT for display: {e}")
            non_geom_cols = [col for col in display_df.columns if col != 'geometry']
            result_df = pd.DataFrame(display_df[non_geom_cols])
            
            # Additional safety check for remaining columns
            for col in result_df.columns:
                if result_df[col].dtype == 'object':
                    sample_values = result_df[col].dropna().head(5)
                    if any(hasattr(val, 'wkt') for val in sample_values if val is not None):
                        result_df[col] = result_df[col].astype(str)
            
            return result_df
    else:
        # No geometry column, just convert to regular DataFrame
        result_df = pd.DataFrame(display_df)
        
        # Safety check for any geometry-like objects in any column
        for col in result_df.columns:
            if result_df[col].dtype == 'object':
                sample_values = result_df[col].dropna().head(5)
                if any(hasattr(val, 'wkt') for val in sample_values if val is not None):
                    result_df[col] = result_df[col].astype(str)
        
        return result_df


def ensure_display_safe_dataframe(df) -> pd.DataFrame:
    """
    Ensure any DataFrame is safe for Streamlit display by converting problematic columns.
    
    Args:
        df: Any DataFrame (pandas or geopandas)
        
    Returns:
        Regular pandas DataFrame safe for display
    """
    if df is None or df.empty:
        return pd.DataFrame()

    # If it's already a regular DataFrame, check for geometry-like columns
    if isinstance(df, pd.DataFrame) and not isinstance(df, gpd.GeoDataFrame):
        # Check if any columns might contain geometry objects
        for col in df.columns:
            if df[col].dtype == 'object':
                sample_val = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                if sample_val is not None and hasattr(sample_val, 'wkt'):
                    # Convert geometry-like objects to WKT strings
                    df = df.copy()
                    df[col] = df[col].apply(
                        lambda x: x.wkt[:100] + "..." if x is not None and hasattr(x, 'wkt') and len(x.wkt) > 100
                        else x.wkt if x is not None and hasattr(x, 'wkt')
                        else str(x) if x is not None
                        else None
                    )
        # Always return a regular DataFrame
        return pd.DataFrame(df)

    # If it's a GeoDataFrame, convert to display-safe DataFrame and ensure it's a pandas DataFrame
    result = prepare_dataframe_for_display(df)
    if isinstance(result, gpd.GeoDataFrame):
        # Should not happen, but just in case
        return pd.DataFrame(result)
    return result


def detect_geometry_columns(df: pd.DataFrame) -> list:
    """
    Detect potential geometry columns in a DataFrame.
    
    Args:
        df: pandas DataFrame to analyze
        
    Returns:
        List of column names that likely contain geometry data
    """
    geometry_columns = []
    
    # Check for columns with common geometry names
    name_patterns = ['geom', 'shape', 'geometry', 'wkt', 'wkb', 'spatial']
    for col in df.columns:
        if any(pattern in col.lower() for pattern in name_patterns):
            geometry_columns.append(col)
            continue
    
    # If no named columns found, check by data type and content
    if not geometry_columns:
        for col in df.columns:
            series = df[col].dropna()
            if series.empty:
                continue
                
            # Check first few values for geometry-like data
            sample_size = min(5, len(series))
            sample_values = series.head(sample_size)
            
            # Check for binary data (WKB)
            if series.dtype == 'object':
                if any(isinstance(val, (bytes, memoryview)) for val in sample_values):
                    geometry_columns.append(col)
                    continue
                    
                # Check for WKT strings (start with common geometry types)
                if any(isinstance(val, str) and val.strip().upper().startswith(('POINT', 'LINESTRING', 'POLYGON', 'MULTIPOINT', 'MULTILINESTRING', 'MULTIPOLYGON', 'GEOMETRYCOLLECTION')) for val in sample_values):
                    geometry_columns.append(col)
                    continue
    
    return geometry_columns