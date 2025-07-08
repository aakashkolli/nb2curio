import sys
from typing import List
import nbformat
from .data_models import CodeCell

class NotebookProcessor:
    """Handles processing of Jupyter notebook files."""
    
    def __init__(self, notebook_path: str):
        self.notebook_path = notebook_path
        self._notebook = None
    
    def get_code_cells(self) -> List[CodeCell]:
        """Extracts all non-empty code cells from the notebook."""
        if self._notebook is None:
            self._load_notebook()
        
        return [
            CodeCell(
                id=cell.metadata.get('id', f'cell_{i}'),
                source=cell.source,
                nb_cell=cell
            )
            for i, cell in enumerate(self._notebook.cells)
            if cell.cell_type == 'code' and cell.source.strip()
        ]
    
    def _load_notebook(self) -> None:
        """Loads the notebook from file."""
        try:
            with open(self.notebook_path, 'r', encoding='utf-8') as f:
                self._notebook = nbformat.read(f, as_version=4)
        except FileNotFoundError:
            print(f"Error: The file '{self.notebook_path}' was not found.")
            sys.exit(1)
        except Exception as e:
            print(f"An error occurred while reading the notebook file: {e}")
            sys.exit(1)
            