import json
import uuid
from typing import Dict, Any, Optional, Tuple
import networkx as nx
from .config import config
from .graph_builder import DependencyGraphBuilder

class CurioConverter:
    """Converts dependency graphs to Curio JSON format."""
    
    def transform_node_content(
        self, source: str, category: str, vega_spec: Optional[Dict], 
        input_var: str, output_var: str
    ) -> str:
        """
        UPDATED: Transforms cell source code using specific input/output variable names
        to preserve original code logic.
        """
        if category == "visualize" and vega_spec:
            # Use the actual input variable name for the data source.
            vega_spec["data"] = {"name": input_var}
            return json.dumps(vega_spec, indent=2)
        
        if category == "load_data":
            # No change needed, this is independent of var names.
            return config.LOAD_DATA_PATTERN.sub(r'import pandas as pd\nreturn \1', source)
        
        if category == "transform":
            # Set up the context by assigning the generic input 'arg' to the correct
            # variable name, then run the user's original code.
            return f"{input_var} = arg\n{source}\nreturn {output_var}"
            
        return source
    
    def dag_to_curio_json(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """
        UPDATED: Converts NetworkX DAG to Curio-compatible JSON, now aware of the
        variable names flowing between nodes.
        """
        graph_no_imports = DependencyGraphBuilder.create_graph_without_imports(graph)
        node_positions = self._calculate_node_positions(graph_no_imports)
        
        # Build a map of target nodes to their primary input variable name from edge data.
        node_input_vars = {
            v: list(d['vars'])[0] 
            for u, v, d in graph.edges(data=True) if d.get('vars')
        }
        
        nx_id_to_uuid = {node_id: str(uuid.uuid4()) for node_id in graph_no_imports.nodes()}
        
        curio_nodes = []
        for node_id, data in graph_no_imports.nodes(data=True):
            input_var = node_input_vars.get(node_id, 'arg')
            defined_vars = data.get('defined_vars', set())
            output_var = list(defined_vars)[0] if defined_vars else input_var
            
            node_content = self.transform_node_content(
                data['source'],
                data['category'],
                data.get('vega_spec'),
                input_var=input_var,
                output_var=output_var
            )

            curio_nodes.append({
                "id": nx_id_to_uuid[node_id],
                "type": config.CATEGORY_TO_CURIO_TYPE.get(data['category'], "DATA_CLEANING"),
                "x": node_positions.get(node_id, (0, 0))[0],
                "y": node_positions.get(node_id, (0, 0))[1],
                "content": node_content,
                "out": "DEFAULT", "in": "DEFAULT", "goal": "", "metadata": {"keywords": []}
            })
        
        curio_edges = [
            {"id": f"reactflow__edge-{nx_id_to_uuid[u]}out-{nx_id_to_uuid[v]}in", "source": nx_id_to_uuid[u], "target": nx_id_to_uuid[v]}
            for u, v in graph_no_imports.edges()
        ]
        
        return {"dataflow": {"nodes": curio_nodes, "edges": curio_edges, "name": "GeneratedWorkflow"}}
    
    def _calculate_node_positions(self, graph: nx.DiGraph) -> Dict[str, Tuple[float, float]]:
        """Calculates optimal positions for nodes in the graph."""
        if not graph.nodes:
            return {}
        try:
            layers = list(nx.topological_generations(graph))
            node_positions = {}
            x, y = config.LAYOUT_SPACING['x'], config.LAYOUT_SPACING['y']
            for i, layer in enumerate(layers):
                start_y = -((len(layer) - 1) * y) / 2
                for j, node_id in enumerate(layer):
                    node_positions[node_id] = (i * x, start_y + j * y)
            return node_positions
        except nx.NetworkXUnfeasible:
            print("Warning: Cycle detected. Using simpler linear layout.")
            return {node_id: (i * config.LAYOUT_SPACING['x'], 0) for i, node_id in enumerate(graph.nodes())}
