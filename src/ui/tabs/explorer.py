"""
Table and map explorer tab UI components.
"""

import streamlit as st
import pydeck as pdk
import pandas as pd

from src.utils.types import GeoDataFrame
from src.utils.constants import BASE_COLORS, DEFAULT_COLOR, DEFAULT_OPACITY, DEFAULT_LINE_WIDTH


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
                color_val = st.color_picker("Feature Color", DEFAULT_COLOR, key="map_color_picker")
                color_rgb = list(int(color_val.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
                filtered_gdf_4326["__color"] = [color_rgb] * len(filtered_gdf_4326)
            else:
                # Generate categorical colors using a simple color palette
                unique_vals = filtered_gdf_4326[color_col].unique()
                # Create a simple color palette
                # Cycle through colors if we have more unique values than colors
                colors = BASE_COLORS * (len(unique_vals) // len(BASE_COLORS) + 1)
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
                    opacity=DEFAULT_OPACITY,
                    stroked=True,
                    filled=True,
                    get_fill_color="__color",
                    get_line_color=[255, 255, 255, 100],
                    get_line_width=DEFAULT_LINE_WIDTH,
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