# GeoData QA Inspector 🔎

A comprehensive Streamlit-based application for Quality Assurance of geospatial data. This tool allows users to upload, inspect, visualize, and compare geospatial datasets with powerful analysis capabilities.

## 🚀 Features

### Data Loading & Support
- **Multiple Formats**: Supports GeoPackage (.gpkg) and GeoParquet (.parquet) files
- **Robust Parsing**: Handles various geometry encodings (WKB, WKT) with fallback mechanisms
- **Error Handling**: Graceful handling of corrupted or invalid geospatial data

### Quality Assurance Tools
- **Data Profiling**: Comprehensive statistics on dataset structure and content
- **Missing Value Analysis**: Identify and quantify missing data across all columns
- **Geometry Validation**: Detect invalid or empty geometries
- **Memory Usage**: Track dataset memory consumption
- **CRS Information**: Display coordinate reference system details

### Visualization & Exploration
- **Interactive Maps**: Visualize geospatial data using PyDeck
- **Data Tables**: Browse and inspect tabular data with sorting and filtering
- **Chart Builder**: Create custom visualizations for attribute data
- **SQL Query Interface**: Execute custom SQL queries on your data using DuckDB

### Comparison Tools
- **Side-by-Side Analysis**: Compare two datasets simultaneously
- **Statistical Comparison**: Identify differences in data distributions
- **Spatial Overlay**: Visualize spatial relationships between datasets

## 📋 Requirements

- Python 3.8+
- Streamlit
- GeoPandas
- PyArrow
- DuckDB
- PyDeck
- Altair

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd quick-qa
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Usage

1. **Start the application**:
   ```bash
   streamlit run app.py
   ```

2. **Open your browser** and navigate to the provided URL (typically `http://localhost:8501`)

3. **Upload your geospatial data**:
   - Use the sidebar to upload GeoPackage (.gpkg) or GeoParquet (.parquet) files
   - The application will automatically load and analyze your data

4. **Explore your data**:
   - **Home**: Overview and quick statistics
   - **Summary**: Detailed QA metrics and data profiling
   - **Table & Map Explorer**: Interactive data browsing and mapping
   - **Chart Builder**: Create custom visualizations
   - **SQL Query**: Execute custom queries on your data
   - **Comparison**: Compare two datasets side-by-side

## 📊 Application Tabs

### Home Tab
- Quick overview of loaded datasets
- Basic statistics and data summary
- Navigation to other analysis tools

### Summary Tab
- Comprehensive data profiling
- Missing value analysis
- Geometry statistics and validation
- Memory usage and performance metrics

### Table & Map Explorer Tab
- Interactive data table with sorting and filtering
- Interactive map visualization using PyDeck
- Attribute-based styling and symbology

### Chart Builder Tab
- Create custom charts for attribute data
- Multiple chart types supported
- Interactive filtering and selection

### SQL Query Tab
- Execute custom SQL queries using DuckDB
- Query results visualization
- Export capabilities

### Comparison Tab
- Side-by-side dataset comparison
- Statistical analysis of differences
- Spatial overlay visualization

## 🔧 Technical Details

### Architecture
- **Frontend**: Streamlit web application
- **Data Processing**: GeoPandas for geospatial operations
- **Database**: DuckDB for SQL queries
- **Visualization**: PyDeck for maps, Altair for charts
- **Caching**: Streamlit caching for performance optimization

### Supported File Formats
- **GeoPackage (.gpkg)**: Native GeoPandas support
- **GeoParquet (.parquet)**: Optimized columnar format with geometry support

### Geometry Handling
- Automatic detection of geometry columns
- Support for WKB and WKT geometry encodings
- Validation of geometry integrity
- CRS (Coordinate Reference System) management

## 🐛 Troubleshooting

### Common Issues

1. **File Loading Errors**:
   - Ensure your file is in a supported format (.gpkg or .parquet)
   - Check that the file contains valid geometry data
   - Verify file permissions

2. **Memory Issues**:
   - Large datasets may require more memory
   - Consider using GeoParquet format for better compression
   - Close other applications to free up memory

3. **Geometry Parsing Errors**:
   - The application includes multiple fallback mechanisms for geometry parsing
   - If parsing fails, the geometry column will be dropped and a warning displayed

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

**Dany Laksono** - July 3, 2025

---

**Note**: This application is designed for geospatial data quality assurance and analysis. It provides comprehensive tools for exploring, validating, and comparing geospatial datasets in an intuitive web interface.
