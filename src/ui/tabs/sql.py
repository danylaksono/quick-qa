"""
SQL query tab UI components for database operations.
"""

import streamlit as st
import pandas as pd

from src.core.database import get_duckdb_connection
from src.utils.types import GeoDataFrame


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