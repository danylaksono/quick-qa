### **Streamlit GeoData QA App:  Requirements**

This document outlines the requirements for a local-first Streamlit application designed for the Quality Assurance (QA) of geospatial data. The app's primary goal is to provide a user-friendly interface for quick data inspection, validation, and comparison.

---

### **1. Core User-Facing Features**

This section defines what the end-user will see and interact with.

#### **1.1. Data Loading and Management**

- **Primary File Upload**: The user must be able to upload a primary geospatial file.
    
    - **Supported Formats**: GeoPackage (`.gpkg`) and GeoParquet (`.parquet`).
        
- **Optional Comparison File**: An optional second file uploader should be available. Uploading a file here will unlock the "Comparison Mode."
    
- **Data Source Display**: Clearly display the name, size, and type of the uploaded file(s).
    

#### **1.2. Main Interface Tabs**

The application interface should be organized into the following tabs for clarity:

- **Summary & QA Tab**: The default view, showing high-level statistics and automated quality checks.
    
- **Table Explorer Tab**: An interactive table view of the data.
    
- **Map Visualizer Tab**: An interactive map to inspect geometries.
    
- **Chart Builder Tab**: Tools to create and view plots from attribute data.
    
- **SQL Query Tab**: An interface for running custom SQL queries.
    
- **Comparison Tab** (Conditional): This tab only appears when a second file is uploaded.
    

#### **1.3. Feature Breakdown by Tab**

##### **Summary & QA Tab**

- **Metadata Panel**: Display key metadata:
    
    - Total number of rows and columns.
        
    - Coordinate Reference System (CRS).
        
    - Geometry type(s) present (e.g., Point, Polygon).
        
    - File size.
        
- **Automated QA Panel ("Sanity Checks")**:
    
    - **Missing Values**: A summary table showing the count and percentage of `NULL` values for each column.
        
    - **Constant Columns**: A list of columns where all values are identical.
        
    - **Geometry Health**: Flags for invalid or empty geometries (requires `geopandas.is_valid`).
        
    - **CRS & BBox Check**: Display the data's bounding box and flag if the CRS is missing.
        

##### **Table Explorer Tab**

- **Interactive Data Table**: Display the attribute data using a performant table component (e.g., `st.dataframe` or `st_aggrid`).
    
- **Column Selection**: Allow the user to show or hide columns.
    
- **Basic Filtering**: Provide simple UI controls to filter rows based on column values.
    

##### **Map Visualizer Tab**

- **Interactive Map**: Render all geometries on a map (`pydeck` or `folium`).
    
    - **Basemap Options**: A dropdown to select the basemap (e.g., OpenStreetMap, Satellite, Carto Positron).
        
    - **Tooltip Inspector**: On hovering over a feature on the map, display its key attributes in a tooltip.
        

##### **Chart Builder Tab**

- **Interactive Charting**:
    
    - **Column Selection**: User selects a column to plot.
        
    - **Chart Type**: Automatically suggest a chart type based on the data type (e.g., **Histogram/KDE** for numeric, **Bar Chart** for categorical).
        
    - **Dynamic Rendering**: Display interactive charts using a library like `altair` or `plotly`.
        

##### **SQL Query Tab**

- **SQL Editor**: A text area for users to write their own SQL queries. The uploaded file will be pre-registered as a table (e.g., `data1`).
    
- **Query Execution**: A "Run" button to execute the query using DuckDB.
    
- **Results Preview**: Display the query output in a data table.
    

##### **Comparison Tab (Conditional)**

- **Attribute Comparison**:
    
    - **Side-by-Side Summary**: Display the summary statistics (mean, min, max, nulls) for common columns next to each other.
        
    - **Distribution Overlays**: For a selected numeric or categorical column, overlay its distribution plots (histograms or bar charts) from both datasets.
        
- **Spatial Comparison**:
    
    - **Map Overlay**: Display both datasets on the same map with different, user-selectable colors.
        
- **Schema Comparison**:
    
    - Highlight columns that are present in one dataset but not the other.
        

#### **1.4. Data Export**

- **Download Filtered Data**: A button to download the current view of the data (after filtering or querying) as a CSV or GeoParquet file.
    
- **Export Report**: A button to generate and download a static HTML file that contains a snapshot of the current summary stats, map view, and active charts.
    

---

### **2. Technical & Development Requirements**

This section outlines the implementation details for the developer.

#### **2.1. Technology Stack**

- **Core Framework**: `streamlit`
    
- **Data Manipulation**: `pandas`, `geopandas`
    
- **SQL Engine**: `duckdb` (with its spatial extension)
    
- **Interactive Mapping**: `pydeck` or `folium`
    
- **Interactive Charting**: `altair` or `plotly`
    

#### **2.2. Development Tasks & Implementation Notes**

**Phase 1: Core App Setup**

1. **File Handling**:
    
    - Use `st.file_uploader` with `type=['gpkg', 'parquet']`.
        
    - Implement a `load_data(uploaded_file)` function that reads the file into a GeoDataFrame and is cached with `@st.cache_data`.
        
2. **UI Scaffolding**:
    
    - Set up the main tabs using `st.tabs`.
        
    - Implement the conditional logic for the second file uploader and the "Comparison" tab.
        

Phase 2: Feature Implementation

3. Summary & QA:

* For metadata, access gdf.shape, gdf.crs, and gdf.geom_type.

* For QA, use gdf.isnull().sum(), gdf.nunique(), and gdf.geometry.is_valid. Display results cleanly using st.metric and st.dataframe.

4. Map Visualization:

* Ensure any input CRS is transformed to EPSG:4326 for web mapping.

* Use st.pydeck_chart for efficient rendering of large datasets.

5. Chart Builder:

* Use st.selectbox to list columns for plotting.

* Write modular functions like create_histogram(df, column) that return a chart object.

6. SQL Integration:

* Create a single DuckDB connection.

* Use conn.register('data1', gdf) to make the DataFrame queryable.

* Wrap the query execution in a try...except block to handle SQL errors gracefully.

Phase 3: Advanced Features & Polish

7. Comparison Logic:

* When the second file is loaded, create two GeoDataFrames (gdf1, gdf2).

* Pass both frames to comparison functions that generate the side-by-side tables and overlaid charts.

8. Performance Optimization:

* Use @st.cache_data and @st.cache_resource appropriately to avoid re-running expensive computations (e.g., data loading, summary stats).

* If a file is very large (e.g., > 500k rows), display a warning and offer to proceed with a random sample (gdf.sample(n=50000)).

9. Export Functionality:

* Use df.to_csv() and st.download_button.

* For the HTML report, generate HTML strings for the components and combine them into a single file.

#### **2.3. Code and Deployment Practices**

- **Modularity**: Structure the app with functions for each distinct piece of logic (e.g., `render_map_tab()`, `calculate_qa_stats()`).
    
- **State Management**: Use Streamlit's session state (`st.session_state`) to manage UI state and avoid unexpected resets.
    
- **Distribution**:
    
    - Include a `requirements.txt` file with all dependencies pinned to specific versions.
        
    - Provide a clear `README.md` with setup and run instructions.
        
    - (Optional) Create a `Dockerfile` for easy, containerized deployment.
        
- **Security & Privacy**: Ensure the app operates entirely on the user's machine with no external data transmission, as specified. This is the default behavior of Streamlit unless external APIs are explicitly called.