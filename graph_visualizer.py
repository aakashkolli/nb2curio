import tkinter as tk
from tkinter import scrolledtext
from typing import Dict, Optional, Any
import matplotlib.pyplot as plt
import networkx as nx
from .config import config
from .graph_builder import DependencyGraphBuilder

class GraphVisualizer:
    """Handles visualization of dependency graphs."""
    
    def visualize_dag(self, graph: nx.DiGraph) -> None:
        """Renders the dependency graph using matplotlib."""
        if not graph.nodes:
            return
        
        fig, ax = plt.subplots(figsize=(16, 10), facecolor='#f0f0f0')
        ax.set_facecolor('#f0f0f0')
        
        graph_no_imports = DependencyGraphBuilder.create_graph_without_imports(graph)
        pos = self._calculate_layout(graph_no_imports)
        
        if pos:
            self._draw_graph(graph_no_imports, pos, ax)
            self._setup_interactivity(fig, graph_no_imports, pos)
            self._add_legend(ax)
        
        self._setup_plot_appearance(fig)
        plt.show()

    def _calculate_layout(self, graph: nx.DiGraph) -> Optional[Dict]:
        """Calculates the optimal layout for the graph."""
        if not graph.nodes: return None
        if nx.is_directed_acyclic_graph(graph):
            for i, layer in enumerate(nx.topological_generations(graph)):
                for node in layer:
                    graph.nodes[node]["layer"] = i
            return nx.multipartite_layout(graph, subset_key="layer")
        else:
            print("\nWarning: Cycles detected. Using spring layout.")
            return nx.spring_layout(graph, seed=42)
    
    def _draw_graph(self, graph: nx.DiGraph, pos: Dict, ax) -> Any:
        """Draws the graph elements."""
        node_data = graph.nodes(data=True)
        labels = {n: f"{d.get('category', 'other').title()}" for n, d in node_data}
        node_colors = [config.NODE_COLORS.get(d.get('category', 'other'), 'gray') for _, d in node_data]
        edge_colors = [config.NODE_BORDERS.get(d.get('category', 'other'), 'black') for _, d in node_data]
        
        nx.draw_networkx_nodes(
            graph, pos, ax=ax, node_size=3500, node_color=node_colors,
            edgecolors=edge_colors, linewidths=1.5
        )
        nx.draw_networkx_edges(
            graph, pos, ax=ax, arrowstyle='-|>', arrowsize=20,
            edge_color='#555555', width=1.5, node_size=3500
        )
        nx.draw_networkx_labels(graph, pos, ax=ax, labels=labels, font_size=9, font_weight='bold')
        
        edge_labels = {(u, v): ", ".join(d.get('vars', [])) for u, v, d in graph.edges(data=True)}
        nx.draw_networkx_edge_labels(
            graph, pos, edge_labels=edge_labels, font_color='black', font_size=8,
            label_pos=0.6, bbox=dict(boxstyle='round,pad=0.2', ec='none', fc='white')
        )
    
    def _setup_interactivity(self, fig, graph: nx.DiGraph, pos: Dict) -> None:
        """Sets up interactive features for the graph."""
        if not fig.gca().collections: return
        nodes_collection = fig.gca().collections[0]
        nodes_collection.set_picker(5)
        node_list = list(graph.nodes)
        
        def on_pick(event):
            if event.artist is not nodes_collection: return
            node_id = node_list[event.ind[0]]
            self._show_code_window(f"Source Code: {node_id[:10]}...", graph.nodes[node_id]['source'])
        
        fig.canvas.mpl_connect('pick_event', on_pick)
    
    def _add_legend(self, ax) -> None:
        """Adds a legend to the plot."""
        legend_handles = [
            plt.Line2D([], [], marker='o', color='w', label=cat.replace('_', ' ').title(),
                       markerfacecolor=color, markersize=12, markeredgecolor=config.NODE_BORDERS[cat])
            for cat, color in config.NODE_COLORS.items()
        ]
        ax.legend(handles=legend_handles, title="Cell Category", loc="upper right")
    
    def _setup_plot_appearance(self, fig) -> None:
        """Sets up the overall appearance of the plot."""
        fig.suptitle("Jupyter Notebook Dependency Graph", fontsize=20, y=0.96)
        fig.text(0.5, 0.92, "(Click Nodes to View Code)", ha='center', fontsize=12, color='gray')
        plt.tight_layout(rect=[0, 0, 1, 0.9])
        plt.box(False)
    
    def _show_code_window(self, title: str, source: str) -> None:
        """Displays a popup window with code."""
        try:
            root = tk.Tk()
            root.title(title)
            root.geometry("500x350")
            text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=25)
            text_area.pack(expand=True, fill='both', padx=5, pady=5)
            text_area.insert(tk.INSERT, source)
            text_area.configure(state='disabled')
            root.mainloop()
        except Exception as e:
            print(f"Could not open code window. Tkinter error: {e}")
