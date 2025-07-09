"""
Dataset comparison tab UI components.
"""

import streamlit as st
import pandas as pd

from src.core.qa_calculator import calculate_qa_stats
from src.utils.types import GeoDataFrame


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