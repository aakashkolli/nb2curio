from dataclasses import dataclass, field
from typing import Set, Optional, Dict, Any

@dataclass
class CellAnalysis:
    """Results of analyzing a code cell."""
    defined_vars: Set[str]
    used_vars: Set[str]
    pure_overwrites: Set[str]
    category: str
    vega_spec: Optional[Dict[str, Any]] = None

@dataclass
class CodeCell:
    """Represents a code cell from a Jupyter notebook."""
    id: str
    source: str
    nb_cell: Any
    