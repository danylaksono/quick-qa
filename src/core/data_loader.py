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

from src.utils.types import GeoDataFrame, FileUpload


def clear_data_cache() -> None:
    """Clears all cached data to free up memory."""
    try:
        st.cache_data.clear()
        st.cache_resource.clear()
        logging.info("Data cache cleared successfully")
    except Exception as e:
        logging.error(f"Error clearing cache: {e}")


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
            df = pd.read_parquet(uploaded_file, engine='pyarrow')
            # Find geometry column by name or type
            geom_cols = [col for col in df.columns if 'geom' in col.lower() or 'shape' in col.lower()]
            if not geom_cols:
                # Try to find by type (bytes/object)
                for col in df.columns:
                    if df[col].dtype == 'object' and any(isinstance(val, (bytes, memoryview)) for val in df[col].dropna()[:5]):
                        geom_cols.append(col)
                        break
            if not geom_cols:
                st.error(f"File '{file_name}' does not contain a geometry column.")
                st.toast(f"❌ Failed to load {file_name}: No geometry column found", icon="❌")
                return None
            geom_col = geom_cols[0]
            geom_series = df[geom_col]
            gdf = None
            # Defensive geometry parsing
            try:
                # Try GeoDataFrame constructor (may work if already parsed)
                gdf = gpd.GeoDataFrame(df, geometry=geom_col)
                if gdf.geometry.isna().all() or gdf.geometry.empty:
                    raise ValueError("No valid geometries found")
            except Exception:
                # Try WKB/WKT parsing
                parsed = False
                # Try WKB for bytes/object
                if geom_series.dtype == 'object' or isinstance(geom_series.iloc[0], (bytes, memoryview)):
                    try:
                        geometries = geom_series.apply(lambda x: wkb.loads(x) if pd.notna(x) else None)
                        parsed = True
                    except Exception:
                        try:
                            geometries = geom_series.apply(lambda x: wkb.loads(bytes(x)) if pd.notna(x) else None)
                            parsed = True
                        except Exception:
                            try:
                                geometries = geom_series.apply(lambda x: wkb.loads(x.tobytes()) if pd.notna(x) else None)
                                parsed = True
                            except Exception:
                                try:
                                    geometries = geom_series.apply(lambda x: wkb.loads(x.encode('latin-1')) if pd.notna(x) else None)
                                    parsed = True
                                except Exception:
                                    pass
                # Try WKT for string columns
                if not parsed and geom_series.dtype == 'object':
                    try:
                        geometries = geom_series.apply(lambda x: wkt.loads(x) if pd.notna(x) else None)
                        parsed = True
                    except Exception:
                        pass
                if parsed:
                    df_clean = df.drop(columns=[geom_col])
                    df_clean['geometry'] = geometries
                    gdf = gpd.GeoDataFrame(df_clean, geometry='geometry')
                else:
                    st.warning(f"Could not parse geometry column '{geom_col}'. It will be dropped.")
                    df_clean = df.drop(columns=[geom_col])
                    gdf = gpd.GeoDataFrame(df_clean)
        else:
            st.error(
                "Unsupported file format. Please upload a GeoPackage (.gpkg) "
                "or GeoParquet (.parquet) file."
            )
            st.toast(f"❌ Failed to load {file_name}: Unsupported format", icon="❌")
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
        
        # Show success toast
        st.toast(f"✅ Successfully loaded {file_name} ({len(gdf)} rows)", icon="✅")
        return gdf
        
    except Exception as e:
        st.error(f"Error loading file '{file_name}': {e}")
        st.toast(f"❌ Failed to load {file_name}: {str(e)[:50]}...", icon="❌")
        logging.error(f"Failed to load {file_name}: {e}")
        return None 