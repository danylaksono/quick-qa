# GeoData QA Inspector

A Streamlit application for quick and efficient Quality Assurance (QA) of geospatial data. Upload, inspect, visualize, and compare geospatial datasets with ease.

Deployed version at: [Quick QA Inspector](https://geodata-inspector.streamlit.app).

## Features

- Upload and inspect GeoPackage (`.gpkg`) and GeoParquet (`.parquet`) files
- Automated summary and QA checks
- Table and map explorer with synchronized filtering
- Chart builder for dynamic data visualization
- SQL query interface for custom analysis
- Side-by-side dataset comparison

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/danylaksono/quick-qa.git
   cd quick-qa
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the Streamlit app:

```bash
streamlit run app.py
```

Open your browser to the provided local URL to access the app.

## How to Use

1. **Upload Data**: Use the sidebar to upload your primary dataset (`.gpkg` or `.parquet`). Optionally, upload a second dataset for comparison.
2. **Explore Tabs**:
   - **Summary & QA**: View high-level data summaries and automated checks.
   - **Table & Map Explorer**: Filter and visualize data on a map.
   - **Chart Builder**: Create charts from your data.
   - **SQL Query**: Run SQL queries on your dataset.
   - **Compare Datasets**: (If two datasets uploaded) Analyze differences side-by-side.

## License

This project is licensed under the MIT License.
