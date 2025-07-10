"""
Summary tab UI components for QA statistics and overview.
"""

import streamlit as st
import pydeck as pdk
import geopandas as gpd

from src.core.qa_calculator import calculate_qa_stats
from src.core.data_loader import prepare_dataframe_for_display
from src.utils.types import GeoDataFrame


def render_summary_tab(gdf: GeoDataFrame, title: str) -> None:
    """Renders the Summary & QA tab."""

    st.header(f"Summary & QA: `{title}`")
    qa_stats = calculate_qa_stats(gdf)

    # --- CRS Plausibility Check ---
    def plausible_for_crs(bbox, crs):
        # Simple heuristics for common CRSs
        if bbox is None or crs is None:
            return True  # Can't check
        try:
            crs_str = crs.to_string() if hasattr(crs, 'to_string') else str(crs)
            minx, miny, maxx, maxy = bbox
            # EPSG:4326 (WGS84): longitude [-180, 180], latitude [-90, 90]
            if "4326" in crs_str or "WGS 84" in crs_str:
                if not (-180 <= minx <= 180 and -180 <= maxx <= 180 and -90 <= miny <= 90 and -90 <= maxy <= 90):
                    return False
            # EPSG:27700 (British National Grid): easting/northing in meters, typical ranges
            if "27700" in crs_str or "OSGB" in crs_str:
                if not (0 <= minx <= 700000 and 0 <= maxx <= 700000 and 0 <= miny <= 1300000 and 0 <= maxy <= 1300000):
                    return False
        except Exception:
            return True
        return True

    crs_mismatch = False
    bbox = qa_stats.get("bbox")
    crs = gdf.crs
    if bbox is not None and crs is not None:
        if not plausible_for_crs(bbox, crs):
            crs_mismatch = True

    if crs_mismatch:
        st.warning("Possible CRS mismatch detected: The assigned CRS does not match the coordinate ranges in the data.\n\nFor example, the CRS is set to EPSG:4326 (WGS84), but the coordinates look like they are in a projected system such as EPSG:27700 (British National Grid).\n\nThis can cause incorrect map display and spatial analysis results.")
        with st.expander("Fix CRS Assignment or Transform Data"):
            st.write("You can either reassign the CRS (set the correct CRS without changing coordinates), or transform the data (convert coordinates to a new CRS).\n\n**Reassign** if the coordinates are correct but the CRS is wrong.\n**Transform** if the CRS is correct but the coordinates need to be converted.")
            crs_options = [
                ("EPSG:4326 (WGS84)", "EPSG:4326"),
                ("EPSG:27700 (British National Grid)", "EPSG:27700"),
                ("EPSG:3857 (Web Mercator)", "EPSG:3857"),
            ]
            crs_label, crs_code = zip(*crs_options)
            selected_idx = 1 if "4326" in str(crs) else 0
            new_crs = st.selectbox("Select CRS to assign or transform to:", crs_label, index=selected_idx)
            action = st.radio("Action", ["Reassign CRS (do not transform coordinates)", "Transform to selected CRS (convert coordinates)"])
            if st.button("Apply CRS Fix", key="crs_fix_btn"):
                import geopandas as gpd
                if action.startswith("Reassign"):
                    gdf.set_crs(crs_code[crs_label.index(new_crs)], inplace=True, allow_override=True)
                    st.success(f"CRS reassigned to {new_crs}.")
                else:
                    gdf.to_crs(crs_code[crs_label.index(new_crs)], inplace=True)
                    st.success(f"Data transformed to {new_crs}.")
                # Recompute QA stats and bbox after fix
                qa_stats.clear()
                qa_stats.update(calculate_qa_stats(gdf))
                bbox = qa_stats.get("bbox")
                crs = gdf.crs
                st.rerun()

    # --- Display Metrics ---
    st.subheader("Key Metrics")
    cols = st.columns(5)
    cols[0].metric("Rows", f"{qa_stats.get('rows', 0):,}")
    cols[1].metric("Columns", f"{qa_stats.get('cols', 0):,}")
    cols[2].metric("Memory Usage", qa_stats.get("memory", "N/A"))
    cols[3].metric("CRS", qa_stats.get("crs", "N/A"))
    # Duplicate Rows Count
    import pandas as pd
    dup_count = gdf.duplicated().sum()
    dup_pct = (dup_count / len(gdf) * 100) if len(gdf) > 0 else 0
    cols[4].metric("Duplicate Rows", f"{dup_count:,} ({dup_pct:.1f}%)")
    # --- Sample Data Preview ---
    st.subheader("Sample Data Preview")
    display_df = prepare_dataframe_for_display(gdf, max_rows=5)
    st.dataframe(display_df, hide_index=True)

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
        else:
            st.info("No geometry column present in this dataset.")

    st.subheader("Bounding Box")
    st.write("**Data Bounding Box:**")
    if qa_stats.get("bbox") is not None:
        st.code(f"{qa_stats['bbox']}")
        # Add map visualization of the bounding box
        st.write("**Bounding Box Map:**")
        try:
            from shapely.geometry import box
            bbox = qa_stats['bbox']
            bbox_geom = box(bbox[0], bbox[1], bbox[2], bbox[3])
            bbox_gdf = gpd.GeoDataFrame({'geometry': [bbox_geom]}, crs=gdf.crs)
            bbox_gdf_4326 = bbox_gdf.to_crs("EPSG:4326")
            center_lat = (bbox_gdf_4326.total_bounds[1] + bbox_gdf_4326.total_bounds[3]) / 2
            center_lon = (bbox_gdf_4326.total_bounds[0] + bbox_gdf_4326.total_bounds[2]) / 2
            # basemap_style = st.selectbox(
            #     "Basemap Style",
            #     options=["light", "dark", "satellite", "road"],
            #     index=0,
            #     key="bbox_basemap"
            # )
            view_state = pdk.ViewState(
                latitude=center_lat,
                longitude=center_lon,
                zoom=8,
                pitch=0
            )
            bbox_layer = pdk.Layer(
                "GeoJsonLayer",
                bbox_gdf_4326,
                opacity=0.3,
                stroked=True,
                filled=True,
                get_fill_color=[255, 0, 0, 100],
                get_line_color=[255, 0, 0, 255],
                get_line_width=3,
                pickable=True,
            )
            crs_string = gdf.crs.to_string() if gdf.crs else "Not defined"
            tooltip = {
                "html": "<b>Bounding Box</b><br/>"
                        f"<b>CRS:</b> {crs_string}<br/>"
                        f"<b>Bounds:</b> {bbox}<br/>"
                        f"<b>Width:</b> {bbox[2] - bbox[0]:.6f}<br/>"
                        f"<b>Height:</b> {bbox[3] - bbox[1]:.6f}"
            }
            st.pydeck_chart(
                pdk.Deck(
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


    # --- Column Info Table ---
    st.subheader("Column Overview")
    import pandas as pd
    # User input for custom null values
    custom_nulls_str = st.text_input(
        "Custom null values (comma-separated, case-insensitive)",
        value=", ",  # default: empty string and space
        help="Specify custom null values to be counted in each column. Example: '', 'N/A', 'none', '-'"
    )
    custom_nulls = [v.strip().lower() for v in custom_nulls_str.split(",") if v.strip() != ""]

    def get_column_dtype(series):
        import pandas as pd
        inferred = pd.api.types.infer_dtype(series, skipna=True)
        mapping = {
            'string': 'string',
            'unicode': 'string',
            'bytes': 'bytes',
            'floating': 'float',
            'integer': 'int',
            'mixed-integer': 'mixed-int',
            'mixed-integer-float': 'mixed-int-float',
            'decimal': 'decimal',
            'complex': 'complex',
            'boolean': 'bool',
            'datetime': 'datetime',
            'datetime64': 'datetime64',
            'timedelta': 'timedelta',
            'timedelta64': 'timedelta64',
            'date': 'date',
            'time': 'time',
            'empty': 'empty',
            'mixed': 'mixed',
            'mixed-integer': 'mixed-int',
            'mixed-integer-float': 'mixed-int-float',
            'categorical': 'category',
            'period': 'period',
            'interval': 'interval',
            'other': 'object',
        }
        if series.name == 'geometry':
            return 'geometry'
        dtype_label = mapping.get(inferred, inferred)
        if dtype_label == 'object':
            unique_types = set(type(x).__name__ for x in series.dropna())
            if len(unique_types) == 1:
                dtype_label = unique_types.pop()
        return dtype_label

    def count_custom_nulls(series, custom_nulls):
        if not custom_nulls:
            return 0
        # Convert all values to string, lower, strip, then count matches
        return series.apply(lambda v: str(v).strip().lower() in custom_nulls if pd.notnull(v) else False).sum()

    col_info = pd.DataFrame({
        "Column Name": gdf.columns,
        "Data Type": [get_column_dtype(gdf[col]) for col in gdf.columns],
        "Unique Values": [gdf[col].nunique(dropna=False) for col in gdf.columns],
        "Duplicate Values": [gdf.shape[0] - gdf[col].nunique(dropna=False) for col in gdf.columns],
        "Custom Null Values": [count_custom_nulls(gdf[col], custom_nulls) for col in gdf.columns],
    })
    # Add a separate column for geometry WKT sample, keep all columns type-consistent
    col_info["Geometry Sample (WKT)"] = ""
    if "geometry" in gdf.columns:
        try:
            col_info.loc[col_info["Column Name"] == "geometry", "Data Type"] = "geometry (WKT)"
            geom_sample = None
            geom_series = gdf["geometry"]
            # Defensive: check for shapely and valid geometry
            if hasattr(geom_series, "dropna"):
                non_null_geoms = geom_series.dropna()
                if not non_null_geoms.empty:
                    first_geom = non_null_geoms.iloc[0]
                    # Defensive: check for wkt attribute
                    wkt_str = getattr(first_geom, "wkt", None)
                    if wkt_str is not None:
                        wkt_preview = wkt_str[:80] + ("..." if len(wkt_str) > 80 else "")
                        col_info.loc[col_info["Column Name"] == "geometry", "Geometry Sample (WKT)"] = wkt_preview
        except Exception:
            col_info.loc[col_info["Column Name"] == "geometry", "Data Type"] = "geometry"
    st.dataframe(col_info, hide_index=True)
    # --- Numeric Columns: Outlier Detection & Value Range ---
    st.subheader("Numeric Columns: Outlier Detection & Value Range")
    import numpy as np
    import altair as alt
    num_cols = [col for col in gdf.select_dtypes(include=[np.number]).columns if col != 'geometry']
    if not num_cols:
        st.info("No numeric columns found.")
    else:
        stats = []
        for col in num_cols:
            s = gdf[col].dropna()
            if s.empty:
                stats.append({
                    "Column": col,
                    "Min": None,
                    "Max": None,
                    "Mean": None,
                    "Median": None,
                    "Std": None,
                    "Outliers (IQR)": None,
                })
                continue
            q1 = s.quantile(0.25)
            q3 = s.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outliers = ((s < lower) | (s > upper)).sum()
            stats.append({
                "Column": col,
                "Min": s.min(),
                "Max": s.max(),
                "Mean": s.mean(),
                "Median": s.median(),
                "Std": s.std(),
                "Outliers (IQR)": outliers,
            })
        st.dataframe(pd.DataFrame(stats), hide_index=True)

        # Violin plots for each numeric column
        st.markdown("**Violin Plots for Numeric Columns**")
        charts = []
        for col in num_cols:
            s = gdf[col].dropna()
            if s.empty:
                continue

            chart = alt.Chart(s.to_frame(name=col)).transform_density(
                col,
                as_=[col, 'density'],
                extent=[float(s.min()), float(s.max())],
                groupby=[]
            ).mark_area(
                orient='horizontal',
                opacity=0.6
            ).encode(
                y=alt.Y(f'{col}:Q', title=col),
                x=alt.X('density:Q', title='Density', stack='center'),
            ).properties(height=280, width=220)

            charts.append(chart)

        # Arrange in rows of N plots (e.g. 3 per row)
        N = 3
        for i in range(0, len(charts), N):
            row = alt.hconcat(*charts[i:i+N])
            st.altair_chart(row, use_container_width=True)
        # for col in num_cols:
        #     s = gdf[col].dropna()
        #     if s.empty:
        #         continue
        #     # Altair violin plot using density transform
        #     base = alt.Chart(s.to_frame(name=col)).transform_density(
        #         col,
        #         as_=[col, 'density'],
        #         extent=[float(s.min()), float(s.max())],
        #         groupby=[]
        #     ).mark_area(
        #         orient='horizontal',
        #         opacity=0.6
        #     ).encode(
        #         y=alt.Y(f'{col}:Q', title=col),
        #         x=alt.X('density:Q', title='Density', stack='center'),
        #     ).properties(height=280, width=220)
        #     st.altair_chart(base, use_container_width=True)

    # --- Data Distribution Plots (Small Multiples with Altair) ---
    st.subheader("Column Data Distributions (Small Multiples)")
    import altair as alt

    def is_bool_like(series):
        if pd.api.types.is_bool_dtype(series):
            return True
        unique_vals = set(series.dropna().unique())
        if unique_vals <= {True, False}:
            return True
        return all(str(v).strip().lower() in {'true', 'false'} for v in unique_vals)

    # Filter suitable columns (exclude geometry, all-unique)
    dist_cols = [
        col for col in gdf.columns
        if col != "geometry" and gdf[col].nunique(dropna=False) < len(gdf)
    ]

    if not dist_cols:
        st.info("No suitable columns for distribution plots.")
    else:
        ncols = min(4, len(dist_cols))
        rows = [dist_cols[i:i + ncols] for i in range(0, len(dist_cols), ncols)]

        for row in rows:
            cols = st.columns(len(row))
            for idx, col in enumerate(row):
                with cols[idx]:
                    s = gdf[col].dropna()
                    # dtype_label = str(gdf[col].dtype)
                    dtype_label = get_column_dtype(gdf[col])
                    st.markdown(f"**{col}** <span style='color:gray'>({dtype_label})</span>", unsafe_allow_html=True)

                    try:
                        if is_bool_like(s):
                            # Convert to canonical bool
                            s_bool = s.map(lambda v: str(v).strip().lower() == 'true')
                            vc = s_bool.value_counts().rename_axis('value').reset_index(name='count')
                            vc['value'] = vc['value'].map({True: 'True', False: 'False'})
                            chart = alt.Chart(vc).mark_bar(color='#457b9d').encode(
                                x=alt.X('value:N', sort=['True', 'False'], title=None),
                                y=alt.Y('count:Q', title='Count')
                            ).properties(height=180, width=150)
                            st.altair_chart(chart, use_container_width=False)

                        elif pd.api.types.is_numeric_dtype(s):
                            chart = alt.Chart(s.to_frame(name=col)).mark_bar(color='#1d3557').encode(
                                x=alt.X(f"{col}:Q", bin=alt.Bin(maxbins=20), title=None),
                                y=alt.Y('count()', title='Count')
                            ).properties(height=180, width=220)
                            st.altair_chart(chart, use_container_width=False)

                        elif pd.api.types.is_categorical_dtype(s) or s.dtype == object:
                            vc = s.value_counts().head(20).rename_axis('value').reset_index(name='count')
                            chart = alt.Chart(vc).mark_bar(color='#a8dadc').encode(
                                x=alt.X('value:N', sort='-y', title=None),
                                y=alt.Y('count:Q', title='Count')
                            ).properties(height=180, width=220)
                            st.altair_chart(chart, use_container_width=False)

                        else:
                            st.text("Distribution not supported for this type.")
                    except Exception as e:
                        st.warning(f"Could not plot {col}: {e}")

    # st.subheader("Column Data Distributions (Small Multiples)")
    # import altair as alt

    # def is_bool_like(series):
    #     # True bool dtype
    #     if pd.api.types.is_bool_dtype(series):
    #         return True
    #     # Object dtype but only True/False/None or 'True'/'False' (case-insensitive)
    #     unique_vals = set(series.dropna().unique())
    #     bool_set = {True, False}
    #     if unique_vals <= bool_set:
    #         return True
    #     # All values are 'true'/'false' strings (case-insensitive)
    #     if all((str(v).strip().lower() in {'true', 'false'}) for v in unique_vals):
    #         return True
    #     return False

    # # Filter columns: skip geometry and columns with all unique values
    # dist_cols = [
    #     col for col in gdf.columns
    #     if col != "geometry" and gdf[col].nunique(dropna=False) < len(gdf)
    # ]
    # if not dist_cols:
    #     st.info("No suitable columns for distribution plots.")
    # else:
    #     ncols = min(4, len(dist_cols))
    #     rows = [dist_cols[i:i+ncols] for i in range(0, len(dist_cols), ncols)]
    #     for row in rows:
    #         cols = st.columns(len(row))
    #         for idx, col in enumerate(row):
    #             with cols[idx]:
    #                 s = gdf[col].dropna()
    #                 # Detect bool-like columns
    #                 if is_bool_like(s):
    #                     dtype_label = "bool"
    #                     # Convert to bool for plotting
    #                     s_bool = s.map(lambda v: True if str(v).strip().lower() == 'true' else False if str(v).strip().lower() == 'false' else None)
    #                 else:
    #                     dtype_label = str(gdf[col].dtype)
    #                     s_bool = None
    #                 st.markdown(f"**{col}** ({dtype_label})")
    #                 try:
    #                     if pd.api.types.is_numeric_dtype(s):
    #                         chart = alt.Chart(s.to_frame(name=col)).mark_bar().encode(
    #                             x=alt.X(f"{col}:Q", bin=alt.Bin(maxbins=20)),
    #                             y=alt.Y('count()', title='Count')
    #                         ).properties(height=180, width=220)
    #                         st.altair_chart(chart, use_container_width=False)
    #                     elif is_bool_like(s):
    #                         # Plot as bar chart with True/False counts
    #                         vc = s_bool.value_counts().rename_axis('value').reset_index(name='count')
    #                         vc['value'] = vc['value'].map({True: 'True', False: 'False'})
    #                         chart = alt.Chart(vc).mark_bar().encode(
    #                             x=alt.X('value:N', sort=['True', 'False'], title=col),
    #                             y=alt.Y('count:Q', title='Count')
    #                         ).properties(height=180, width=120)
    #                         st.altair_chart(chart, use_container_width=False)
    #                     elif pd.api.types.is_categorical_dtype(s) or s.dtype == object:
    #                         vc = s.value_counts().head(20).rename_axis('value').reset_index(name='count')
    #                         chart = alt.Chart(vc).mark_bar().encode(
    #                             x=alt.X('value:N', sort='-y', title=col),
    #                             y=alt.Y('count:Q', title='Count')
    #                         ).properties(height=180, width=220)
    #                         st.altair_chart(chart, use_container_width=False)
    #                     else:
    #                         st.text("Distribution not shown for this type.")
    #                 except Exception as e:
    #                     st.warning(f"Could not plot {col}: {e}")