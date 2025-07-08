from collections import defaultdict
from typing import List, Dict
import networkx as nx
from .code_analyzer import CodeAnalyzer
from .data_models import CodeCell, CellAnalysis
from .config import config

class DependencyGraphBuilder:
    """Builds dependency graphs from analyzed code cells."""
    
    def __init__(self, analyzer: CodeAnalyzer):
        self.analyzer = analyzer
    
    def build_graph(self, code_cells: List[CodeCell]) -> nx.DiGraph:
        """Builds a dependency graph from code cells."""
        graph = nx.DiGraph()
        cell_analyses = {
            cell.id: self.analyzer.analyze_dependencies(cell.source)
            for cell in code_cells
        }

        for cell in code_cells:
            analysis = cell_analyses[cell.id]
            # UPDATED: Store defined_vars on the node to be used later in conversion.
            graph.add_node(
                cell.id,
                source=cell.source,
                category=analysis.category,
                vega_spec=analysis.vega_spec,
                nb_cell=cell.nb_cell,
                defined_vars=analysis.defined_vars
            )
        
        categorized_cells = defaultdict(list)
        for cell in code_cells:
            categorized_cells[cell_analyses[cell.id].category].append(cell)

        logically_ordered_cells = [
            cell for category in config.LOGICAL_CELL_ORDER
            for cell in categorized_cells[category]
        ]
        
        self._add_dependency_edges(graph, logically_ordered_cells, cell_analyses)
        return graph
    
    def _add_dependency_edges(self, graph: nx.DiGraph, code_cells: List[CodeCell], 
                              cell_analyses: Dict[str, CellAnalysis]) -> None:
        """Adds dependency edges to the graph."""
        cell_ids = [cell.id for cell in code_cells]
        
        for i, current_cell_id in enumerate(cell_ids):
            current_analysis = cell_analyses[current_cell_id]
            relevant_vars = current_analysis.used_vars - current_analysis.pure_overwrites
            
            for var in relevant_vars:
                for j in range(i - 1, -1, -1):
                    prev_cell_id = cell_ids[j]
                    if var in cell_analyses[prev_cell_id].defined_vars:
                        if graph.has_edge(prev_cell_id, current_cell_id):
                            graph[prev_cell_id][current_cell_id]['vars'].add(var)
                        else:
                            graph.add_edge(prev_cell_id, current_cell_id, vars={var})
                        break
    
    @staticmethod
    def create_graph_without_imports(graph: nx.DiGraph) -> nx.DiGraph:
        """Creates a copy of the graph without import nodes."""
        graph_no_imports = graph.copy()
        import_nodes = [
            node for node, data in graph.nodes(data=True) 
            if data.get('category') == 'imports'
        ]
        graph_no_imports.remove_nodes_from(import_nodes)
        return graph_no_imports
