"""
Summary tab UI components for QA statistics and overview.
"""

import streamlit as st
import pydeck as pdk
import geopandas as gpd

from src.core.qa_calculator import calculate_qa_stats
from src.utils.types import GeoDataFrame


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
        if not qa_stats.get("missing_values", st.empty()).empty:
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
            st.dataframe(qa_stats.get("geom_types", st.empty()).to_frame(name="Count"))
            
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