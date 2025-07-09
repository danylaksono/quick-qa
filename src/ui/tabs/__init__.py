"""
Tab UI components for the GeoData QA application.
"""

from .home import render_home_tab
from .summary import render_summary_tab
from .explorer import render_table_and_map_explorer_tab
from .charts import render_chart_builder_tab
from .sql import render_sql_query_tab
from .comparison import render_comparison_tab

__all__ = [
    "render_home_tab",
    "render_summary_tab", 
    "render_table_and_map_explorer_tab",
    "render_chart_builder_tab",
    "render_sql_query_tab",
    "render_comparison_tab"
] 