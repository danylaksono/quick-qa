"""
Chart builder tab UI components for data visualization.
"""

import streamlit as st
import pandas as pd

from src.core.data_loader import prepare_dataframe_for_display
from src.utils.types import GeoDataFrame
from src.utils.constants import CHART_TYPES, HISTOGRAM_BINS_RANGE


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

    # Create a display-safe DataFrame for Altair charts
    chart_df = prepare_dataframe_for_display(gdf)

    numeric_cols = chart_df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = chart_df.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    if not numeric_cols and not categorical_cols:
        st.warning("No plottable (numeric or categorical) columns found.")
        return

    plot_type = st.selectbox("Select plot type", options=CHART_TYPES)

    if plot_type == "Histogram (Numeric)":
        if not numeric_cols:
            st.warning("No numeric columns available for a histogram.")
            return
        col_to_plot = st.selectbox("Select a numeric column:", options=numeric_cols)
        bins = st.slider("Number of bins", *HISTOGRAM_BINS_RANGE)
        chart = (
            alt.Chart(chart_df)
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
            alt.Chart(chart_df)
            .mark_bar()
            .encode(
                x=alt.X(f"{col_to_plot}:N", sort="-y"),
                y="count()",
                tooltip=[col_to_plot, "count()"],
            )
            .properties(title=f"Distribution of {col_to_plot}")
        )
        st.altair_chart(chart, use_container_width=True)

    # Data Exploration Panel using pygwalker (StreamlitRenderer)
    with st.expander("🔍 Data Exploration (Pygwalker)", expanded=False):
        st.markdown("Explore your data interactively with [Pygwalker](https://github.com/Kanaries/pygwalker). You can save your chart state in the UI.")
        try:
            from pygwalker.api.streamlit import StreamlitRenderer, init_streamlit_comm
        except ImportError:
            st.error("Pygwalker is not installed. Please run `pip install pygwalker`.")
            return
        
        # Initialize pygwalker communication
        init_streamlit_comm()
        
        # Convert GeoDataFrame to DataFrame if needed for pygwalker
        # Use a more robust conversion that ensures no geometry objects remain
        try:
            df = prepare_dataframe_for_display(gdf)
            
            # Additional safety check: ensure no geometry objects remain
            if 'geometry' in df.columns:
                # Convert geometry column to string representation
                df = df.copy()
                df['geometry'] = df['geometry'].astype(str)
            
            # Check for any remaining geometry-like objects in any column
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Sample a few values to check for geometry objects
                    sample_values = df[col].dropna().head(3)
                    if any(hasattr(val, 'wkt') for val in sample_values if val is not None):
                        # Convert to string representation
                        df[col] = df[col].astype(str)
            
            # Ensure it's a pure pandas DataFrame
            df = pd.DataFrame(df)
            
        except Exception as e:
            st.error(f"Error preparing data for PyGWalker: {e}")
            st.info("Trying fallback conversion...")
            try:
                # Fallback: drop geometry column entirely
                if hasattr(gdf, 'geometry') and 'geometry' in gdf.columns:
                    df = gdf.drop(columns=['geometry'])
                else:
                    df = pd.DataFrame(gdf)
            except Exception as fallback_error:
                st.error(f"Fallback conversion also failed: {fallback_error}")
                return
        
        @st.cache_resource
        def get_pyg_renderer(_df):
            return StreamlitRenderer(_df, spec="./gw_config.json", debug=False)
        
        try:
            renderer = get_pyg_renderer(df)
            st.subheader("Display Explore UI")
            tab1, tab2 = st.tabs([
                "graphic walker", "data profiling"
            ])
            with tab1:
                renderer.explorer()
            with tab2:
                renderer.explorer(default_tab="data", key="pyg_explorer_1")
        except Exception as e:
            st.error(f"PyGWalker initialization failed: {e}")
            st.info("This might be due to unsupported data types. Try uploading a different file or check the data format.")