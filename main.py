import argparse
import json
from .notebook_processor import NotebookProcessor
from .code_analyzer import CodeAnalyzer
from .graph_builder import DependencyGraphBuilder
from .curio_converter import CurioConverter
from .graph_visualizer import GraphVisualizer

class NotebookConverter:
    """Main converter class that orchestrates the conversion process."""
    
    def __init__(self, notebook_path: str):
        self.notebook_path = notebook_path
        self.processor = NotebookProcessor(notebook_path)
        self.analyzer = CodeAnalyzer()
        self.graph_builder = DependencyGraphBuilder(self.analyzer)
        self.curio_converter = CurioConverter()
        self.visualizer = GraphVisualizer()
    
    def convert_to_curio(self, output_path: str) -> None:
        """Converts the notebook to Curio JSON format."""
        print(f"\nAnalyzing notebook: {self.notebook_path}")
        code_cells = self.processor.get_code_cells()
        
        if not code_cells:
            print("No code cells found in the notebook.")
            return
        
        print("\nBuilding dependency graph...")
        dependency_graph = self.graph_builder.build_graph(code_cells)
        
        print("\nGenerating Curio JSON...")
        curio_dataflow = self.curio_converter.dag_to_curio_json(dependency_graph)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(curio_dataflow, f, indent=2)
            print(f"\nSuccessfully generated Curio dataflow at: {output_path}")
        except Exception as e:
            print(f"\nError writing to output file: {e}")
    
    def visualize(self) -> None:
        """Visualizes the notebook dependency graph."""
        print(f"\nAnalyzing notebook: {self.notebook_path}")
        code_cells = self.processor.get_code_cells()
        
        if not code_cells:
            print("No code cells found in the notebook.")
            return
        
        print("\nBuilding dependency graph...")
        dependency_graph = self.graph_builder.build_graph(code_cells)
        
        print("\nVisualizing graph...")
        self.visualizer.visualize_dag(dependency_graph)

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Convert a Jupyter Notebook into a Curio dataflow JSON or an interactive graph."
    )
    parser.add_argument("notebook_path", help="The file path to the Jupyter Notebook (.ipynb).")
    parser.add_argument("-o", "--output", help="The file path to save the output Curio JSON.", default=None)
    parser.add_argument("--visualize", action="store_true", help="Visualize the dependency graph instead of generating JSON.")
    args = parser.parse_args()
    
    converter = NotebookConverter(args.notebook_path)
    
    if args.visualize:
        converter.visualize()
    elif args.output:
        converter.convert_to_curio(args.output)
    else:
        print("\nNo output action specified. Use --output <file> to generate JSON or --visualize to see the graph.")

if __name__ == "__main__":
    main()
