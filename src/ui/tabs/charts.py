"""
Chart builder tab UI components for data visualization.
"""

import streamlit as st
import pandas as pd

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

    numeric_cols = gdf.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = gdf.select_dtypes(
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
        df = gdf.copy()
        if hasattr(df, "geometry"):
            df["geometry_wkt"] = df["geometry"].apply(lambda g: g.wkt if g is not None else None)
            df = df.drop(columns=["geometry"])  # Remove geometry column to avoid duckdb error
        @st.cache_resource
        def get_pyg_renderer(_df):
            return StreamlitRenderer(_df, spec="./gw_config.json", debug=False)
        renderer = get_pyg_renderer(df)
        st.subheader("Display Explore UI")
        tab1, tab2 = st.tabs([
            "graphic walker", "data profiling"
        ])
        with tab1:
            renderer.explorer()
        with tab2:
            renderer.explorer(default_tab="data", key="pyg_explorer_1")