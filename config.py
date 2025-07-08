import re
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    """Configuration constants for the converter."""
    NODE_COLORS = {
        "imports": "#cde4ff", "load_data": "#d4edda", "transform": "#fff3cd",
        "visualize": "#f8d7da", "other": "#e2e3e5",
    }
    NODE_BORDERS = {
        "imports": "#5b9bd5", "load_data": "#57a465", "transform": "#c7a84a",
        "visualize": "#c85a62", "other": "#6c757d",
    }
    CATEGORY_TO_CURIO_TYPE = {
        "load_data": "DATA_LOADING",
        "transform": "DATA_CLEANING",
        "visualize": "VIS_VEGA",
    }
    VIZ_KEYWORDS = frozenset(['.plot', 'plt.show', 'sns.', 'px.', 'go.Figure', 'alt.Chart', '"$schema"'])
    DATA_KEYWORDS = frozenset(['read_csv', 'read_excel', 'read_sql'])
    LAYOUT_SPACING = {'x': 800, 'y': 500}
    LOGICAL_CELL_ORDER = ["imports", "load_data", "transform", "visualize", "other"]

    # Compiled regex patterns for better performance
    MAGIC_PATTERN = re.compile(r'^\s*%.*$', re.MULTILINE)
    SHELL_PATTERN = re.compile(r'^\s*!.*$', re.MULTILINE)
    LOAD_DATA_PATTERN = re.compile(r'^\s*\w+\s*=\s*(pd\.read_.*)', re.MULTILINE)

config = Config()
