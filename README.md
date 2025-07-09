# GeoData QA Inspector - Modular Version

A modular Streamlit application for Quality Assurance of geospatial data. This version has been refactored from the original monolithic `app.py` into a well-organized, maintainable package structure.

## 🏗️ Architecture

The application has been refactored into a modular structure with clear separation of concerns:

```
src/
├── __init__.py                 # Package initialization
├── main.py                     # Main application orchestrator
├── core/                       # Core business logic
│   ├── __init__.py
│   ├── data_loader.py         # File loading and parsing
│   ├── qa_calculator.py       # Quality assurance calculations
│   └── database.py            # Database connections
├── ui/                         # User interface components
│   ├── __init__.py
│   ├── sidebar.py             # Sidebar and file uploads
│   └── tabs/                  # Tab-specific UI components
│       ├── __init__.py
│       ├── home.py            # Welcome and instructions
│       ├── summary.py         # QA statistics and overview
│       ├── explorer.py        # Table and map visualization
│       ├── charts.py          # Data visualization charts
│       ├── sql.py             # SQL query interface
│       └── comparison.py      # Dataset comparison
└── utils/                      # Utilities and constants
    ├── __init__.py
    ├── constants.py           # Configuration constants
    └── types.py              # Type hints and aliases
```

## 🚀 Quick Start

### Option 1: Run the modular version directly

```bash
streamlit run app_modular.py
```

### Option 2: Install as a package

```bash
pip install -e .
streamlit run app_modular.py
```

## 📦 Module Overview

### Core Modules (`src/core/`)

- **`data_loader.py`**: Handles file uploads and parsing of GeoPackage and GeoParquet files
- **`qa_calculator.py`**: Calculates quality assurance statistics (missing values, geometry health, etc.)
- **`database.py`**: Manages DuckDB connections for SQL queries

### UI Modules (`src/ui/`)

- **`sidebar.py`**: File upload interface and session state management
- **`tabs/`**: Individual tab components for different app functionalities

### Utility Modules (`src/utils/`)

- **`constants.py`**: Centralized configuration values and constants
- **`types.py`**: Type hints and aliases for better code documentation

## 🔧 Key Improvements

### 1. **Separation of Concerns**
- Business logic separated from UI components
- Clear module responsibilities
- Easier to test individual components

### 2. **Maintainability**
- Smaller, focused files
- Clear imports and dependencies
- Consistent code structure

### 3. **Extensibility**
- Easy to add new tabs or features
- Modular design allows for independent development
- Clear interfaces between components

### 4. **Type Safety**
- Comprehensive type hints
- Better IDE support and error detection
- Self-documenting code

## 🧪 Testing

The modular structure makes it easier to test individual components:

```python
# Example: Test data loading
from src.core.data_loader import load_data

# Example: Test QA calculations
from src.core.qa_calculator import calculate_qa_stats
```

## 🔄 Migration from Original

The original `app.py` has been preserved. To use the modular version:

1. **Keep using the original**: `streamlit run app.py`
2. **Switch to modular**: `streamlit run app_modular.py`

Both versions provide identical functionality, but the modular version is more maintainable and extensible.

## 📋 Dependencies

The modular version uses the same dependencies as the original:

- `streamlit` - Web application framework
- `geopandas` - Geospatial data handling
- `pandas` - Data manipulation
- `pydeck` - Map visualization
- `duckdb` - SQL database
- `altair` - Chart creation (optional)
- `shapely` - Geometry processing

## 🛠️ Development

### Adding New Features

1. **New Tab**: Create a new file in `src/ui/tabs/`
2. **New Core Functionality**: Add to `src/core/`
3. **New Constants**: Add to `src/utils/constants.py`

### Code Style

- Follow PEP 8 guidelines
- Use type hints throughout
- Add docstrings to all functions
- Keep modules focused and single-purpose

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions, please open an issue on GitHub. 