# GeoData QA App
#
# This script creates a Streamlit application for Quality Assurance of geospatial data.
# It allows users to upload, inspect, visualize, and compare geospatial datasets.
#
# Author: Dany Laksono
# Date: July 3, 2025

import io
import logging
import os
import tempfile
from typing import Dict, Optional, Tuple, List, Any, Union

import duckdb
import geopandas as gpd
import pandas as pd
import pydeck as pdk # noqa
import streamlit as st

# Import shapely for geometry parsing
try:
    from shapely import wkb, wkt
    from shapely.errors import ShapelyError
except ImportError:
    # Shapely might not be available, but we'll handle this gracefully
    pass

# --- Configuration ---
st.set_page_config(
    page_title="GeoData QA Inspector",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Setup basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Type Hinting Aliases ---
GeoDataFrame = gpd.GeoDataFrame
DataFrame = pd.DataFrame
PydeckChart = pdk.Deck
AltairChart = Any # Using Any for Altair to avoid dependency if not used everywhere
DuckDBCon = duckdb.DuckDBPyConnection

# --- State Management ---
# Initialize session state keys to ensure they exist.
if "gdf1" not in st.session_state:
    st.session_state["gdf1"] = None
if "gdf2" not in st.session_state:
    st.session_state["gdf2"] = None
if "gdf1_name" not in st.session_state:
    st.session_state["gdf1_name"] = None
if "gdf2_name" not in st.session_state:
    st.session_state["gdf2_name"] = None


# --- Caching and Data Loading ---
@st.cache_data(show_spinner="Loading data...")
def load_data(uploaded_file: io.BytesIO, file_name: str) -> Optional[GeoDataFrame]:
    """
    Loads a geospatial file into a GeoDataFrame.
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


@st.cache_data(show_spinner="Calculating QA stats...")
def calculate_qa_stats(_gdf: GeoDataFrame) -> Dict[str, Any]:
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


@st.cache_resource
def get_duckdb_connection() -> DuckDBCon:
    """Creates and returns a DuckDB connection."""
    return duckdb.connect(database=":memory:", read_only=False)


# --- UI Rendering Functions ---
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
            type=["gpkg", "parquet"],
            key="primary_uploader",
        )

        if uploaded_file_1:
            st.session_state.gdf1 = load_data(uploaded_file_1, uploaded_file_1.name)
            st.session_state.gdf1_name = uploaded_file_1.name

        st.header("Comparison Dataset (Optional)")
        uploaded_file_2 = st.file_uploader(
            "Upload a second file to enable comparison",
            type=["gpkg", "parquet"],
            key="secondary_uploader",
        )

        if uploaded_file_2:
            st.session_state.gdf2 = load_data(uploaded_file_2, uploaded_file_2.name)
            st.session_state.gdf2_name = uploaded_file_2.name
        
        st.info("Geodata QA Inspector - v.1.0.0 2025")


def render_home_tab() -> None:
    """Renders the welcome and instructions tab."""
    # st.image("https://user-images.githubusercontent.com/2675629/234909123-524729c7-2c2c-416b-9cf6-339c7ac4656f.png", width=150)
    st.title("Welcome to the GeoData QA Inspector!")
    st.markdown(
        """
        This application is designed for quick and efficient Quality Assurance (QA) of your geospatial data.

        ### How to Use This App:

        1.  **Upload Data**: Use the sidebar on the left to upload your primary dataset. Supported formats are **GeoPackage (`.gpkg`)** and **GeoParquet (`.parquet`)**.
        2.  **Explore**: Once uploaded, navigate through the tabs to explore your data:
            - **Summary & QA**: Get a high-level overview and automated quality checks.
            - **Table & Map Explorer**: View and filter the raw attribute data with synchronized map visualization.
            - **Chart Builder**: Create dynamic charts from your data's attributes.
            - **SQL Query**: Run custom SQL queries directly on your data.
        3.  **Compare (Optional)**: Upload a second dataset in the sidebar to unlock the **Compare Datasets** tab. This mode allows for powerful side-by-side analysis of two datasets.

        Start by uploading a file in the sidebar!
        """
    )


def render_summary_tab(gdf: GeoDataFrame, title: str) -> None:
    """Renders the Summary & QA tab."""
    st.header(f"Summary & QA: `{title}`")
    qa_stats = calculate_qa_stats(gdf)

    if not qa_stats:
        st.warning("Could not generate QA statistics.")
        return

    # --- Display Metrics ---
    st.subheader("Key Metrics")
    cols = st.columns(4)
    cols[0].metric("Rows", f"{qa_stats.get('rows', 0):,}")
    cols[1].metric("Columns", f"{qa_stats.get('cols', 0):,}")
    cols[2].metric("Memory Usage", qa_stats.get("memory", "N/A"))
    cols[3].metric("CRS", qa_stats.get("crs", "N/A"))

    # --- Display Detailed Stats ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Missing Values")
        if not qa_stats.get("missing_values", pd.Series()).empty:
            st.dataframe(qa_stats["missing_values"].to_frame(name="Null Count"))
        else:
            st.success("No missing values found. ✅")

        st.subheader("Constant Value Columns")
        if qa_stats.get("constant_columns"):
            st.warning("The following columns contain only one unique value:")
            st.json(qa_stats["constant_columns"])
        else:
            st.success("No constant value columns found. ✅")

    with col2:
        st.subheader("Geometry Health")
        if "geometry" in gdf.columns:
            st.metric("Invalid Geometries", f"{qa_stats.get('invalid_geoms', 0):,}")
            if qa_stats.get("invalid_geoms", 0) > 0:
                st.warning("Invalid geometries detected. These may cause errors in spatial operations.")
            
            st.metric("Empty Geometries", f"{qa_stats.get('empty_geoms', 0):,}")
            
            st.write("**Geometry Types:**")
            st.dataframe(qa_stats.get("geom_types", pd.Series()).to_frame(name="Count"))
            
            st.write("**Bounding Box:**")
            if qa_stats.get("bbox") is not None:
                st.code(f"{qa_stats['bbox']}")
                
                # Add map visualization of the bounding box
                st.write("**Bounding Box Map:**")
                try:
                    # Create a simple bounding box visualization
                    from shapely.geometry import box
                    
                    # Get the bounding box coordinates
                    bbox = qa_stats['bbox']
                    # bbox format: [minx, miny, maxx, maxy]
                    bbox_geom = box(bbox[0], bbox[1], bbox[2], bbox[3])
                    
                    # Create a GeoDataFrame with the bounding box
                    bbox_gdf = gpd.GeoDataFrame(
                        {'geometry': [bbox_geom]}, 
                        crs=gdf.crs
                    )
                    
                    # Reproject to WGS84 for web mapping
                    bbox_gdf_4326 = bbox_gdf.to_crs("EPSG:4326")
                    
                    # Calculate center point for the map view
                    center_lat = (bbox_gdf_4326.total_bounds[1] + bbox_gdf_4326.total_bounds[3]) / 2
                    center_lon = (bbox_gdf_4326.total_bounds[0] + bbox_gdf_4326.total_bounds[2]) / 2
                    
                    # Basemap selector for context
                    basemap_style = st.selectbox(
                        "Basemap Style",
                        options=["light", "dark", "satellite", "road"],
                        index=0,
                        key="bbox_basemap"
                    )
                    
                    # Create view state
                    view_state = pdk.ViewState(
                        latitude=center_lat,
                        longitude=center_lon,
                        zoom=8,
                        pitch=0
                    )
                    
                    # Create the bounding box layer
                    bbox_layer = pdk.Layer(
                        "GeoJsonLayer",
                        bbox_gdf_4326,
                        opacity=0.3,
                        stroked=True,
                        filled=True,
                        get_fill_color=[255, 0, 0, 100],  # Red with transparency
                        get_line_color=[255, 0, 0, 255],   # Solid red border
                        get_line_width=3,
                        pickable=True,
                    )
                    
                    # Create tooltip with safe CRS handling
                    crs_string = gdf.crs.to_string() if gdf.crs else "Not defined"
                    tooltip = {
                        "html": "<b>Bounding Box</b><br/>"
                                f"<b>CRS:</b> {crs_string}<br/>"
                                f"<b>Bounds:</b> {bbox}<br/>"
                                f"<b>Width:</b> {bbox[2] - bbox[0]:.6f}<br/>"
                                f"<b>Height:</b> {bbox[3] - bbox[1]:.6f}"
                    }
                    
                    # Render the map with selected basemap
                    st.pydeck_chart(
                        pdk.Deck(
                            map_style=f"mapbox://styles/mapbox/{basemap_style}-v9",
                            initial_view_state=view_state,
                            layers=[bbox_layer],
                            tooltip=tooltip,
                        )
                    )
                    
                except Exception as e:
                    st.error(f"Could not create bounding box map: {e}")
                    st.info("Map visualization requires valid geometries and CRS.")
            else:
                st.info("No bounding box could be determined.")
        else:
            st.info("No geometry column present in this dataset.")


def render_table_and_map_explorer_tab(gdf: GeoDataFrame) -> None:
    """Renders the combined table and map explorer tab."""
    st.header("Table & Map Explorer")
    st.info("Inspect the raw attribute data and see it visualized on the map. Filter the table to see the corresponding features highlighted on the map.")

    # Check if we have valid geometries for mapping
    has_valid_geometries = "geometry" in gdf.columns and not gdf.geometry.is_empty.all()
    
    if not has_valid_geometries:
        st.warning("No valid geometries to display on the map. Only table functionality will be available.")

    # Column selector
    all_cols = gdf.columns.tolist()
    default_cols = [col for col in all_cols if col != 'geometry']
    
    with st.expander("Filter and Select Columns", expanded=True):
        selected_cols = st.multiselect(
            "Select columns to display:", options=all_cols, default=default_cols
        )
        
        if not selected_cols:
            st.warning("Please select at least one column to display.")
            return

        # Simple filter UI
        filter_col = st.selectbox("Filter by column:", options=["None"] + selected_cols)
        filtered_gdf = gdf.copy()  # Create a copy to avoid modifying original
        if filter_col != "None":
            unique_vals = filtered_gdf[filter_col].dropna().unique()
            if len(unique_vals) < 50: # Avoid slow UI for high-cardinality columns
                filter_val = st.multiselect(f"Select values for '{filter_col}':", options=unique_vals)
                if filter_val:
                    filtered_gdf = filtered_gdf[filtered_gdf[filter_col].isin(filter_val)]
            else:
                filter_text = st.text_input(f"Enter text to filter '{filter_col}' (case-insensitive):")
                if filter_text:
                    filtered_gdf = filtered_gdf[filtered_gdf[filter_col].astype(str).str.contains(filter_text, case=False, na=False)]

    # Display filtered data count
    st.info(f"Showing {len(filtered_gdf)} of {len(gdf)} records")

    # Create two columns for table and map
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📊 Data Table")
        display_df = filtered_gdf[selected_cols].copy()
        # Always convert geometry to WKT string for display, if DataFrame
        if isinstance(display_df, pd.DataFrame) and 'geometry' in display_df.columns:
            display_df['geometry'] = display_df['geometry'].apply(lambda x: x.wkt if hasattr(x, 'wkt') else str(x))
        st.dataframe(display_df, use_container_width=True)
        if isinstance(filtered_gdf, pd.DataFrame):
            export_df = filtered_gdf[selected_cols].copy()
            if isinstance(export_df, pd.DataFrame) and 'geometry' in export_df.columns:
                export_df['geometry'] = export_df['geometry'].apply(lambda x: x.wkt if hasattr(x, 'wkt') else str(x))
            st.download_button(
                "Download Data as CSV",
                export_df.to_csv(index=False),
                "filtered_data.csv",
                "text/csv",
                key="download-csv",
            )

    with col2:
        if has_valid_geometries:
            st.subheader("🗺️ Map View")
            
            # Reproject to WGS84 for web mapping
            try:
                filtered_gdf_4326 = filtered_gdf.to_crs("EPSG:4326")
            except Exception as e:
                st.error(f"Could not reproject data to EPSG:4326 for mapping: {e}")
                return

            # Map Controls
            basemap = st.selectbox(
                "Basemap Style",
                options=["road", "satellite", "dark", "light"],
                index=2,
                key="map_basemap"
            )
            
            # Color options
            color_col = st.selectbox(
                "Color by Attribute (Optional)", 
                options=["Constant"] + [col for col in filtered_gdf.columns if hasattr(filtered_gdf[col], 'dtype') and filtered_gdf[col].dtype in ['object', 'category', 'int64', 'bool']],
                key="map_color_col"
            )

            if color_col == "Constant":
                color_val = st.color_picker("Feature Color", "#00A4FF", key="map_color_picker")
                color_rgb = list(int(color_val.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
                filtered_gdf_4326["__color"] = [color_rgb] * len(filtered_gdf_4326)
            else:
                # Generate categorical colors using a simple color palette
                unique_vals = filtered_gdf_4326[color_col].unique()
                # Create a simple color palette
                base_colors = [
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
                
                # Cycle through colors if we have more unique values than colors
                colors = base_colors * (len(unique_vals) // len(base_colors) + 1)
                colors = colors[:len(unique_vals)]
                
                color_map = {val: colors[i] for i, val in enumerate(unique_vals)}
                # Use apply instead of map for better type compatibility
                filtered_gdf_4326["__color"] = filtered_gdf_4326[color_col].apply(lambda x: color_map.get(x, [0, 0, 0]))
                st.write(f"Color Legend for **{color_col}**:")
                for val, color in color_map.items():
                    st.markdown(f"<span style='color:rgb{tuple(color)};'>■</span> {val}", unsafe_allow_html=True)

            # Pydeck Rendering
            if len(filtered_gdf_4326) > 0:
                midpoint = (
                    filtered_gdf_4326.total_bounds[1] + filtered_gdf_4326.total_bounds[3]
                ) / 2, (filtered_gdf_4326.total_bounds[0] + filtered_gdf_4326.total_bounds[2]) / 2
                
                view_state = pdk.ViewState(
                    latitude=midpoint[0], longitude=midpoint[1], zoom=10, pitch=45
                )

                layer = pdk.Layer(
                    "GeoJsonLayer",
                    filtered_gdf_4326,
                    opacity=0.8,
                    stroked=True,
                    filled=True,
                    get_fill_color="__color",
                    get_line_color=[255, 255, 255, 100],
                    get_line_width=10,
                    pickable=True,
                )

                tooltip_cols = [col for col in filtered_gdf.columns if col != "geometry"]
                tooltip = {"html": ""}
                if tooltip_cols:
                    tooltip_html = "<b>Feature Attributes</b><br/>" + "<br/>".join(
                        [f"<b>{col}:</b> {{{col}}}" for col in tooltip_cols]
                    )
                    tooltip = {"html": tooltip_html}
                
                st.pydeck_chart(
                    pdk.Deck(
                        map_style=f"mapbox://styles/mapbox/{basemap}-v9",
                        initial_view_state=view_state,
                        layers=[layer],
                        tooltip=tooltip,
                    )
                )
            else:
                st.info("No features to display on the map after filtering.")
        else:
            st.info("No valid geometries available for mapping.")


def render_chart_builder_tab(gdf: GeoDataFrame) -> None:
    """Renders the chart builder tab."""
    st.header("Chart Builder")
    st.info("Create charts to explore attribute distributions.")
    
    # Lazy import altair
    try:
        import altair as alt
    except ImportError:
        st.error("Altair is not installed. Please run `pip install altair`.")
        return

    numeric_cols = gdf.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = gdf.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    if not numeric_cols and not categorical_cols:
        st.warning("No plottable (numeric or categorical) columns found.")
        return

    plot_type = st.selectbox(
        "Select plot type", options=["Histogram (Numeric)", "Bar Chart (Categorical)"]
    )

    if plot_type == "Histogram (Numeric)":
        if not numeric_cols:
            st.warning("No numeric columns available for a histogram.")
            return
        col_to_plot = st.selectbox("Select a numeric column:", options=numeric_cols)
        bins = st.slider("Number of bins", 5, 100, 20)
        chart = (
            alt.Chart(gdf)
            .mark_bar()
            .encode(
                x=alt.X(f"{col_to_plot}:Q", bin=alt.Bin(maxbins=bins)),
                y="count()",
                tooltip=[col_to_plot, "count()"],
            )
            .properties(title=f"Histogram of {col_to_plot}")
        )
        st.altair_chart(chart, use_container_width=True)

    elif plot_type == "Bar Chart (Categorical)":
        if not categorical_cols:
            st.warning("No categorical columns available for a bar chart.")
            return
        col_to_plot = st.selectbox(
            "Select a categorical column:", options=categorical_cols
        )
        chart = (
            alt.Chart(gdf)
            .mark_bar()
            .encode(
                x=alt.X(f"{col_to_plot}:N", sort="-y"),
                y="count()",
                tooltip=[col_to_plot, "count()"],
            )
            .properties(title=f"Distribution of {col_to_plot}")
        )
        st.altair_chart(chart, use_container_width=True)


def render_sql_query_tab(gdf: GeoDataFrame, name: str) -> None:
    """Renders the SQL query tab."""
    st.header("SQL Query Runner")
    st.info(f"Run DuckDB SQL queries directly on your dataset (registered as `{name}`).")

    # Convert GeoDataFrame to regular DataFrame for DuckDB compatibility
    # Convert geometry to WKT format so it can be queried as text
    df_for_duckdb = gdf.copy()
    if 'geometry' in df_for_duckdb.columns:
        df_for_duckdb['geometry'] = df_for_duckdb['geometry'].astype(str)

    con = get_duckdb_connection()
    con.register(name, df_for_duckdb)

    query = st.text_area(
        "Enter your SQL query:",
        value=f"SELECT * FROM {name} LIMIT 10;",
        height=200,
    )

    if st.button("Run Query"):
        try:
            with st.spinner("Executing query..."):
                result_df = con.execute(query).fetchdf()
            st.success("Query executed successfully!")
            st.dataframe(result_df)
            st.download_button(
                "Download Results as CSV",
                result_df.to_csv(index=False),
                "query_results.csv",
            )
        except Exception as e:
            st.error(f"SQL Error: {e}")


def render_comparison_tab(
    gdf1: GeoDataFrame, gdf2: GeoDataFrame, name1: str, name2: str
) -> None:
    """Renders the dataset comparison tab."""
    st.header("Compare Datasets")
    st.info(f"Comparing `{name1}` (Dataset 1) vs. `{name2}` (Dataset 2)")

    # --- Schema Comparison ---
    with st.expander("Schema Comparison", expanded=True):
        cols1 = set(gdf1.columns)
        cols2 = set(gdf2.columns)
        common_cols = list(cols1.intersection(cols2))
        
        st.subheader("Column Overview")
        col1, col2, col3 = st.columns(3)
        col1.metric(f"Columns in `{name1}`", len(cols1))
        col2.metric(f"Columns in `{name2}`", len(cols2))
        col3.metric("Common Columns", len(common_cols))

        if cols1 - cols2:
            st.warning(f"Columns only in `{name1}`: `{list(cols1 - cols2)}`")
        if cols2 - cols1:
            st.warning(f"Columns only in `{name2}`: `{list(cols2 - cols1)}`")
        if not (cols1 - cols2) and not (cols2 - cols1):
            st.success("Both datasets have the exact same columns. ✅")

    # --- Summary Comparison ---
    with st.expander("Summary Statistics Comparison", expanded=True):
        stats1 = calculate_qa_stats(gdf1)
        stats2 = calculate_qa_stats(gdf2)
        
        summary_data = {
            "Metric": ["Rows", "Columns", "CRS", "Invalid Geoms", "Empty Geoms"],
            name1: [
                stats1.get('rows', 'N/A'), stats1.get('cols', 'N/A'),
                stats1.get('crs', 'N/A'), stats1.get('invalid_geoms', 'N/A'),
                stats1.get('empty_geoms', 'N/A')
            ],
            name2: [
                stats2.get('rows', 'N/A'), stats2.get('cols', 'N/A'),
                stats2.get('crs', 'N/A'), stats2.get('invalid_geoms', 'N/A'),
                stats2.get('empty_geoms', 'N/A')
            ]
        }
        st.table(pd.DataFrame(summary_data))

    # --- Distribution Comparison ---
    with st.expander("Attribute Distribution Comparison", expanded=False):
        numeric_cols = [c for c in common_cols if pd.api.types.is_numeric_dtype(gdf1[c]) and pd.api.types.is_numeric_dtype(gdf2[c])]
        if not numeric_cols:
            st.info("No common numeric columns to compare distributions.")
        else:
            col_to_compare = st.selectbox("Select a numeric column to compare:", options=numeric_cols)
            
            # Lazy import altair
            try:
                import altair as alt
            except ImportError:
                st.error("Altair is not installed. Please run `pip install altair`.")
                return

            # Prepare data for Altair - ensure it's a proper DataFrame
            df1_plot = gdf1[[col_to_compare]].copy()
            df1_plot['dataset'] = name1
            df2_plot = gdf2[[col_to_compare]].copy()
            df2_plot['dataset'] = name2
            combined_df = pd.concat([df1_plot, df2_plot], ignore_index=True)
            
            # Ensure combined_df is a proper DataFrame
            combined_df = pd.DataFrame(combined_df)

            chart = alt.Chart(combined_df).mark_area(opacity=0.5).encode(
                x=alt.X(f"{col_to_compare}:Q", bin=alt.Bin(maxbins=50), title=col_to_compare),
                y=alt.Y('count()', stack=None, title='Count'),
                color='dataset:N'
            ).properties(title=f"Distribution Comparison for {col_to_compare}")
            st.altair_chart(chart, use_container_width=True)


# --- Main App Logic ---
def main() -> None:
    """Main function to run the Streamlit app."""
    render_sidebar()

    # Define tabs
    tab_names = ["🏠 Home"]
    if st.session_state.get("gdf1") is not None:
        tab_names.extend(
            [
                "📊 Summary & QA",
                "📊🗺️ Table & Map Explorer",
                "📈 Chart Builder",
                "🔎 SQL Query",
            ]
        )
    if st.session_state.get("gdf1") is not None and st.session_state.get("gdf2") is not None:
        tab_names.append("🆚 Compare Datasets")

    tabs = st.tabs(tab_names)
    
    # Conditional tab rendering
    with tabs[0]:
        render_home_tab()

    if "📊 Summary & QA" in tab_names:
        with tabs[tab_names.index("📊 Summary & QA")]:
            render_summary_tab(st.session_state.gdf1, st.session_state.gdf1_name)

    if "📊🗺️ Table & Map Explorer" in tab_names:
        with tabs[tab_names.index("📊🗺️ Table & Map Explorer")]:
            render_table_and_map_explorer_tab(st.session_state.gdf1)

    if "📈 Chart Builder" in tab_names:
        with tabs[tab_names.index("📈 Chart Builder")]:
            render_chart_builder_tab(st.session_state.gdf1)

    if "🔎 SQL Query" in tab_names:
        with tabs[tab_names.index("🔎 SQL Query")]:
            render_sql_query_tab(st.session_state.gdf1, "data1")

    if "🆚 Compare Datasets" in tab_names:
        with tabs[tab_names.index("🆚 Compare Datasets")]:
            render_comparison_tab(
                st.session_state.gdf1,
                st.session_state.gdf2,
                st.session_state.gdf1_name,
                st.session_state.gdf2_name,
            )


if __name__ == "__main__":
    main()
