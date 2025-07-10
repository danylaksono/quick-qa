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

            # Show map if geometry column exists and is not empty
            if "geometry" in result_df.columns:
                try:
                    import geopandas as gpd
                    import pydeck as pdk
                    from shapely.errors import WKTReadingError

                    # Try to detect CRS from result_df if available
                    crs = None
                    if hasattr(result_df, 'crs') and result_df.crs:
                        crs = result_df.crs
                    # Try to get CRS from a column if present
                    if crs is None and 'crs' in result_df.columns:
                        crs = result_df['crs'].iloc[0]
                    # Let user set CRS if not found or ambiguous
                    if not crs:
                        st.warning("CRS (Coordinate Reference System) not detected in result. Please specify the CRS for correct map display.")
                        crs_input = st.text_input("Enter CRS (e.g., 'EPSG:4326')", value="EPSG:4326", key="crs_input")
                        crs = crs_input
                    else:
                        st.info(f"Detected CRS: {crs}")

                    # Create GeoDataFrame from WKT
                    try:
                        gdf_result = gpd.GeoDataFrame(
                            result_df,
                            geometry=gpd.GeoSeries.from_wkt(result_df["geometry"]),
                            crs=crs
                        )
                    except WKTReadingError as wkt_e:
                        st.warning(f"Could not parse geometry: {wkt_e}")
                        gdf_result = None

                    if gdf_result is not None and not gdf_result.empty:
                        # Reproject to EPSG:4326 for mapping if needed
                        if str(gdf_result.crs).upper() not in ["EPSG:4326", "4326"]:
                            try:
                                gdf_result = gdf_result.to_crs("EPSG:4326")
                            except Exception as crs_e:
                                st.warning(f"Could not reproject to EPSG:4326: {crs_e}")

                        geojson = gdf_result.__geo_interface__
                        bounds = gdf_result.total_bounds  # (minx, miny, maxx, maxy)
                        center_lat = (bounds[1] + bounds[3]) / 2
                        center_lon = (bounds[0] + bounds[2]) / 2
                        # Prepare tooltip fields (show all non-geometry columns)
                        tooltip_fields = [col for col in gdf_result.columns if col != "geometry"]
                        tooltip = {"html": "<b>" + "</b><br><b>".join([f"{col}: {{{col}}}" for col in tooltip_fields]) + "</b>", "style": {"backgroundColor": "steelblue", "color": "white"}}
                        st.pydeck_chart(pdk.Deck(
                            layers=[
                                pdk.Layer(
                                    "GeoJsonLayer",
                                    data=geojson,
                                    pickable=True,
                                    stroked=True,
                                    filled=True,
                                    extruded=False,
                                    get_fill_color=[255, 0, 0, 100],
                                    get_line_color=[0, 0, 0, 200],
                                ),
                            ],
                            initial_view_state=pdk.ViewState(
                                latitude=center_lat,
                                longitude=center_lon,
                                zoom=10,
                                pitch=0,
                            ),
                            tooltip=tooltip,
                        ))
                except Exception as map_e:
                    st.warning(f"Could not render map: {map_e}")

            st.download_button(
                "Download Results as CSV",
                result_df.to_csv(index=False),
                "query_results.csv",
            )
            # Parquet download option
            import io
            parquet_buffer = io.BytesIO()
            try:
                result_df.to_parquet(parquet_buffer, index=False)
                st.download_button(
                    "Download Results as Parquet",
                    parquet_buffer.getvalue(),
                    "query_results.parquet",
                )
            except Exception as pq_e:
                st.warning(f"Could not export to Parquet: {pq_e}")
        except Exception as e:
            st.error(f"SQL Error: {e}")