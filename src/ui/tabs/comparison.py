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
        only1 = list(cols1 - cols2)
        only2 = list(cols2 - cols1)

        st.subheader("Column Overview")
        col1, col2, col3 = st.columns(3)
        col1.metric(f"Columns in `{name1}`", len(cols1))
        col2.metric(f"Columns in `{name2}`", len(cols2))
        col3.metric("Common Columns", len(common_cols))

        # Table showing column presence in each dataset
        st.subheader("Column Presence Table")
        presence_rows = []
        for col in sorted(cols1 | cols2):
            presence_rows.append({
                "Column": col,
                f"In {name1}": "✅" if col in cols1 else "-",
                f"In {name2}": "✅" if col in cols2 else "-"
            })
        presence_df = pd.DataFrame(presence_rows)
        st.dataframe(presence_df, use_container_width=True)

        if only1:
            st.warning(f"Columns only in `{name1}`: `{only1}`")
        if only2:
            st.warning(f"Columns only in `{name2}`: `{only2}`")
        if not only1 and not only2:
            st.success("Both datasets have the exact same columns. ✅")

        # --- Data type mapping function (from summary.py) ---
        def get_column_dtype(series):
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

        # Data types and sample values table (with mapped types)
        st.subheader("Column Data Types and Sample Values")
        schema_rows = []
        for col in sorted(cols1 | cols2):
            if col in gdf1.columns:
                dtype1 = get_column_dtype(gdf1[col])
            else:
                dtype1 = "-"
            if col in gdf2.columns:
                dtype2 = get_column_dtype(gdf2[col])
            else:
                dtype2 = "-"
            sample1 = gdf1[col].dropna().iloc[0] if col in gdf1.columns and not gdf1[col].dropna().empty else "-"
            sample2 = gdf2[col].dropna().iloc[0] if col in gdf2.columns and not gdf2[col].dropna().empty else "-"
            mismatch = dtype1 != dtype2 and dtype1 != "-" and dtype2 != "-"
            schema_rows.append({
                "Column": col,
                f"Type {name1}": dtype1,
                f"Type {name2}": dtype2,
                f"Sample {name1}": sample1,
                f"Sample {name2}": sample2,
                "Type Mismatch": "❌" if mismatch else "None"
            })
        schema_df = pd.DataFrame(schema_rows)
        st.dataframe(schema_df, use_container_width=True)

    # --- Summary Comparison ---
    with st.expander("Summary Statistics Comparison", expanded=True):
        st.subheader("Summary Statistics")
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

        # Numeric column stats - side-by-side and visual comparison
        st.subheader("Numeric Column Statistics")
        numeric_cols = [c for c in gdf1.columns if pd.api.types.is_numeric_dtype(gdf1[c]) and c in gdf2.columns and pd.api.types.is_numeric_dtype(gdf2[c])]
        if numeric_cols:
            stat_names = ["min", "max", "mean", "median", "std", "missing", "unique"]
            for col in numeric_cols:
                s1 = gdf1[col]
                s2 = gdf2[col]
                stats = {
                    "Statistic": stat_names,
                    name1: [s1.min(), s1.max(), s1.mean(), s1.median(), s1.std(), s1.isnull().sum(), s1.nunique()],
                    name2: [s2.min(), s2.max(), s2.mean(), s2.median(), s2.std(), s2.isnull().sum(), s2.nunique()],
                }
                st.markdown(f"**{col}**")
                st.table(pd.DataFrame(stats))

            # Enhanced Numeric Column Statistics Table with color feedback
            stat_names = ["min", "max", "mean", "median", "std", "missing", "unique"]
            for col in numeric_cols:
                s1 = gdf1[col]
                s2 = gdf2[col]
                stats1 = [s1.min(), s1.max(), s1.mean(), s1.median(), s1.std(), s1.isnull().sum(), s1.nunique()]
                stats2 = [s2.min(), s2.max(), s2.mean(), s2.median(), s2.std(), s2.isnull().sum(), s2.nunique()]
                data = {
                    "Statistic": stat_names,
                    f"{name1}": stats1,
                    f"{name2}": stats2
                }
                df = pd.DataFrame(data)
                # Only color the value columns, not the Statistic column
                def color_cells(val, col_idx, row_idx):
                    # Compare values in the two columns for each row
                    if col_idx == 0:
                        return ''
                    v1 = df.iloc[row_idx, 1]
                    v2 = df.iloc[row_idx, 2]
                    if pd.isna(v1) and pd.isna(v2):
                        return 'background-color: #d4edda'
                    elif v1 == v2:
                        return 'background-color: #d4edda'
                    else:
                        return 'background-color: #f8d7da'
                def style_func(val, row_idx, col_idx):
                    return color_cells(val, col_idx, row_idx)
                def styler_applymap(s):
                    # s is a DataFrame
                    styled = pd.DataFrame('', index=s.index, columns=s.columns)
                    for row_idx in range(len(s)):
                        for col_idx in range(len(s.columns)):
                            styled.iloc[row_idx, col_idx] = style_func(s.iloc[row_idx, col_idx], row_idx, col_idx)
                    return styled
                styled = df.style.apply(styler_applymap, axis=None)
                st.markdown(f"**{col}**")
                st.dataframe(styled, use_container_width=True, hide_index=True)
        else:
            st.info("No common numeric columns for detailed statistics.")

        # Null/missing value counts for all columns
        st.subheader("Missing/Null Value Counts (All Columns)")
        null_rows = []
        for col in sorted(set(gdf1.columns) | set(gdf2.columns)):
            null1 = gdf1[col].isnull().sum() if col in gdf1.columns else '-'
            null2 = gdf2[col].isnull().sum() if col in gdf2.columns else '-'
            null_rows.append({
                "Column": col,
                f"{name1} missing": null1,
                f"{name2} missing": null2
            })
        null_df = pd.DataFrame(null_rows)
        st.dataframe(null_df, use_container_width=True)

    # --- Distribution Comparison ---
    with st.expander("Attribute Distribution Comparison", expanded=False):
        numeric_cols = [c for c in common_cols if pd.api.types.is_numeric_dtype(gdf1[c]) and pd.api.types.is_numeric_dtype(gdf2[c])]
        cat_cols = [c for c in common_cols if pd.api.types.is_categorical_dtype(gdf1[c]) or pd.api.types.is_object_dtype(gdf1[c])]
        try:
            import altair as alt
        except ImportError:
            st.error("Altair is not installed. Please run `pip install altair`.")
            return

        if numeric_cols:
            st.subheader("Numeric Column Distribution")
            col_to_compare = st.selectbox("Select a numeric column to compare:", options=numeric_cols, key="num_dist")
            df1_plot = gdf1[[col_to_compare]].copy()
            df1_plot['dataset'] = name1
            df2_plot = gdf2[[col_to_compare]].copy()
            df2_plot['dataset'] = name2
            combined_df = pd.concat([df1_plot, df2_plot], ignore_index=True)
            combined_df = pd.DataFrame(combined_df)

            # Area (histogram) plot
            chart = alt.Chart(combined_df).mark_area(opacity=0.5).encode(
                x=alt.X(f"{col_to_compare}:Q", bin=alt.Bin(maxbins=50), title=col_to_compare),
                y=alt.Y('count()', stack=None, title='Count'),
                color='dataset:N'
            ).properties(title=f"Distribution Comparison for {col_to_compare}")
            st.altair_chart(chart, use_container_width=True)

            # Boxplot
            st.subheader("Boxplot")
            box_chart = alt.Chart(combined_df).mark_boxplot(extent='min-max').encode(
                x=alt.X('dataset:N', title='Dataset'),
                y=alt.Y(f'{col_to_compare}:Q', title=col_to_compare),
                color='dataset:N'
            ).properties(title=f"Boxplot for {col_to_compare}")
            st.altair_chart(box_chart, use_container_width=True)

            # Violin plot (approximate using density)
            st.subheader("Violin Plot (Density)")
            violin_chart = alt.Chart(combined_df).transform_density(
                col_to_compare,
                as_=[col_to_compare, 'density'],
                groupby=['dataset']
            ).mark_area(opacity=0.5).encode(
                x=alt.X(f'{col_to_compare}:Q', title=col_to_compare),
                y=alt.Y('density:Q', title='Density'),
                color='dataset:N'
            ).properties(title=f"Violin Plot for {col_to_compare}")
            st.altair_chart(violin_chart, use_container_width=True)
        else:
            st.info("No common numeric columns to compare distributions.")

        # Categorical column comparison
        if cat_cols:
            st.subheader("Categorical Column Value Counts")
            cat_col = st.selectbox("Select a categorical column to compare:", options=cat_cols, key="cat_dist")
            df1_cat = gdf1[cat_col].value_counts().reset_index()
            df1_cat.columns = [cat_col, 'count']
            df1_cat['dataset'] = name1
            df2_cat = gdf2[cat_col].value_counts().reset_index()
            df2_cat.columns = [cat_col, 'count']
            df2_cat['dataset'] = name2
            cat_combined = pd.concat([df1_cat, df2_cat], ignore_index=True)
            cat_chart = alt.Chart(cat_combined).mark_bar().encode(
                x=alt.X(f'{cat_col}:N', title=cat_col),
                y=alt.Y('count:Q', title='Count'),
                color='dataset:N',
                column=alt.Column('dataset:N', title='Dataset')
            ).properties(title=f"Value Counts for {cat_col}")
            st.altair_chart(cat_chart, use_container_width=True)

        # Multi-column scatter plot
        if len(numeric_cols) >= 2:
            st.subheader("Scatter Plot (Joint Distribution)")
            cols_selected = st.multiselect("Select two numeric columns:", options=numeric_cols, default=numeric_cols[:2], key="scatter_cols")
            if len(cols_selected) == 2:
                df1_scat = gdf1[list(cols_selected)].copy()
                df1_scat['dataset'] = name1
                df2_scat = gdf2[list(cols_selected)].copy()
                df2_scat['dataset'] = name2
                scat_combined = pd.concat([df1_scat, df2_scat], ignore_index=True)
                scat_chart = alt.Chart(scat_combined).mark_circle(opacity=0.5).encode(
                    x=alt.X(f'{cols_selected[0]}:Q'),
                    y=alt.Y(f'{cols_selected[1]}:Q'),
                    color='dataset:N',
                    tooltip=['dataset'] + cols_selected
                ).properties(title=f"Scatter Plot: {cols_selected[0]} vs {cols_selected[1]}")
                st.altair_chart(scat_chart, use_container_width=True)


    # --- Change Detection Panel ---
    with st.expander("Change Detection", expanded=False):
        st.subheader("Detect Changes Between Datasets")
        def find_id_candidates(df):
            candidates = []
            for col in df.columns:
                if str(col).lower() in ["id", "idx", "index"]:
                    candidates.append(col)
            unique_cols = [col for col in df.columns if df[col].is_unique and df[col].notnull().all()]
            for col in unique_cols:
                if col not in candidates:
                    candidates.append(col)
            return candidates

        id_candidates1 = find_id_candidates(gdf1)
        id_candidates2 = find_id_candidates(gdf2)
        common_id_candidates = list(set(id_candidates1) & set(id_candidates2))
        if not common_id_candidates:
            unique1 = [col for col in gdf1.columns if gdf1[col].is_unique and gdf1[col].notnull().all()]
            unique2 = [col for col in gdf2.columns if gdf2[col].is_unique and gdf2[col].notnull().all()]
            common_id_candidates = list(set(unique1) & set(unique2))

        if not common_id_candidates:
            st.warning("No suitable reference (ID) column found in both datasets. Change detection requires a common unique column.")
        else:
            ref_col = st.selectbox(
                "Select reference column for change detection:",
                options=common_id_candidates,
                key="change_ref_col"
            )
            if gdf1[ref_col].isnull().any() or gdf2[ref_col].isnull().any():
                st.error(f"Reference column '{ref_col}' contains null values in one of the datasets. Please clean your data.")
            elif not gdf1[ref_col].is_unique or not gdf2[ref_col].is_unique:
                st.error(f"Reference column '{ref_col}' is not unique in one of the datasets. Please ensure uniqueness.")
            else:
                try:
                    compare_cols = [c for c in gdf1.columns if c in gdf2.columns and c != ref_col]
                    merged = pd.merge(
                        gdf1[[ref_col] + compare_cols],
                        gdf2[[ref_col] + compare_cols],
                        on=ref_col,
                        how="inner",
                        suffixes=(f"_{name1}", f"_{name2}")
                    )
                    changes = []
                    for col in compare_cols:
                        col1 = f"{col}_{name1}"
                        col2 = f"{col}_{name2}"
                        diff_mask = ~(merged[col1].eq(merged[col2]) | (merged[col1].isna() & merged[col2].isna()))
                        changed_rows = merged.loc[diff_mask, [ref_col, col1, col2]]
                        for _, row in changed_rows.iterrows():
                            changes.append({
                                ref_col: row[ref_col],
                                "Column": col,
                                f"{name1}": row[col1],
                                f"{name2}": row[col2]
                            })
                    ids1 = set(gdf1[ref_col])
                    ids2 = set(gdf2[ref_col])
                    added_ids = sorted(list(ids2 - ids1))
                    removed_ids = sorted(list(ids1 - ids2))
                    if changes:
                        st.write(f"Detected {len(changes)} changed value(s):")
                        changes_df = pd.DataFrame(changes)
                        st.dataframe(changes_df, use_container_width=True)
                    else:
                        st.success("No changed values detected for common features.")
                    if added_ids:
                        st.warning(f"IDs only in `{name2}` (added): {added_ids[:10]}{' ...' if len(added_ids)>10 else ''}")
                    if removed_ids:
                        st.warning(f"IDs only in `{name1}` (removed): {removed_ids[:10]}{' ...' if len(removed_ids)>10 else ''}")
                except Exception as e:
                    st.error(f"Error during change detection: {e}")

    # --- Map Comparison Panel ---
    # with st.expander("Map Comparison", expanded=False):
    #     st.subheader("Side-by-Side Map Comparison with Attribute Filtering")
    #     import folium
    #     from streamlit_folium import st_folium
    #     try:
    #         from ipywidgets import jslink, VBox
    #         from folium import Map
    #     except ImportError:
    #         st.warning("ipywidgets is not installed. Map linking will be disabled. Run `pip install ipywidgets` for best experience.")
    #         jslink = None

    #     st.markdown("**Filter features by attribute** (e.g., `ID = 1234`)")
    #     filter_col = st.selectbox("Select attribute to filter by:", options=sorted(list(set(gdf1.columns) & set(gdf2.columns))), key="map_filter_col")
    #     unique_vals1 = sorted(gdf1[filter_col].dropna().unique())
    #     unique_vals2 = sorted(gdf2[filter_col].dropna().unique())
    #     common_vals = sorted(list(set(unique_vals1) & set(unique_vals2)))
    #     if not common_vals:
    #         st.warning(f"No common values for '{filter_col}' in both datasets.")
    #     else:
    #         selected_val = st.selectbox(f"Select value for '{filter_col}':", options=common_vals, key="map_filter_val")
    #         filtered1 = gdf1[gdf1[filter_col] == selected_val]
    #         filtered2 = gdf2[gdf2[filter_col] == selected_val]
    #         col1, col2 = st.columns(2)
    #         def get_center(gdf):
    #             if gdf.empty:
    #                 return [0, 0]
    #             try:
    #                 centroid = gdf.geometry.centroid.unary_union.centroid
    #                 return [centroid.y, centroid.x]
    #             except Exception:
    #                 return [0, 0]

    #         # --- Map sync state ---
    #         if 'map_center' not in st.session_state:
    #             st.session_state['map_center'] = get_center(filtered1 if not filtered1.empty else filtered2)
    #         if 'map_zoom' not in st.session_state:
    #             st.session_state['map_zoom'] = 14

    #         def update_map_state(map_data):
    #             if map_data and 'center' in map_data and 'zoom' in map_data:
    #                 center = map_data['center']
    #                 # st_folium returns {'lat': ..., 'lng': ...}, folium expects [lat, lng]
    #                 if isinstance(center, dict) and 'lat' in center and 'lng' in center:
    #                     st.session_state['map_center'] = [center['lat'], center['lng']]
    #                 else:
    #                     st.session_state['map_center'] = center
    #                 st.session_state['map_zoom'] = map_data['zoom']

    #         def get_map_center():
    #             center = st.session_state['map_center']
    #             if isinstance(center, dict) and 'lat' in center and 'lng' in center:
    #                 return [center['lat'], center['lng']]
    #             return center

    #         with col1:
    #             st.markdown(f"**{name1}**")
    #             if not filtered1.empty:
    #                 m1 = folium.Map(location=get_map_center(), zoom_start=st.session_state['map_zoom'])
    #                 folium.GeoJson(
    #                     filtered1.__geo_interface__,
    #                     tooltip=folium.GeoJsonTooltip(fields=[filter_col], aliases=[filter_col]),
    #                     popup=folium.GeoJsonPopup(fields=[c for c in filtered1.columns if c != 'geometry'], aliases=[c for c in filtered1.columns if c != 'geometry'], max_width=300)
    #                 ).add_to(m1)
    #                 map_data1 = st_folium(m1, width=400, height=400, key="map1")
    #                 update_map_state(map_data1)
    #             else:
    #                 st.info("No features to show.")
    #         with col2:
    #             st.markdown(f"**{name2}**")
    #             if not filtered2.empty:
    #                 m2 = folium.Map(location=get_map_center(), zoom_start=st.session_state['map_zoom'])
    #                 folium.GeoJson(
    #                     filtered2.__geo_interface__,
    #                     tooltip=folium.GeoJsonTooltip(fields=[filter_col], aliases=[filter_col]),
    #                     popup=folium.GeoJsonPopup(fields=[c for c in filtered2.columns if c != 'geometry'], aliases=[c for c in filtered2.columns if c != 'geometry'], max_width=300)
    #                 ).add_to(m2)
    #                 map_data2 = st_folium(m2, width=400, height=400, key="map2")
    #                 update_map_state(map_data2)
    #             else:
    #                 st.info("No features to show.")
    #         st.caption("Map view is synchronized between the two maps. Pan or zoom either map to update both.")