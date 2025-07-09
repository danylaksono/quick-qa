"""
Home tab UI components for welcome and instructions.
"""

import streamlit as st


def render_home_tab() -> None:
    """Renders the welcome and instructions tab."""
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